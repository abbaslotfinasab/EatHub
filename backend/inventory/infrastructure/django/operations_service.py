"""Transactional orchestration for Inventory operation documents.

The documents hold workflow/audit metadata only. Quantities and valuation are
always changed through the existing V1 Stock aggregate and appended ledger.
"""
from decimal import Decimal

from django.db.models import Q, Subquery
from django.utils import timezone

from inventory.application.exceptions import OperationConflict, ResourceNotFound
from inventory.application.commands import OperationIdentityInput, ReverseStockMovementCommand
from inventory.application.context import InventoryExecutionContext
from inventory.application.use_cases.reverse_stock_movement import ReverseStockMovementUseCase
from inventory.domain.entities.stock import Stock
from inventory.domain.value_objects.quantity import Quantity
from inventory.domain.value_objects.source_identity import SourceIdentity
from inventory.domain.value_objects.unit import Unit
from inventory.domain.value_objects.unit_cost import UnitCost
from inventory.infrastructure.django.mappers import (
    movement_to_orm, stock_to_domain,
    warehouse_to_domain,
)
from inventory.infrastructure.django.models import (
    InventoryOperation, InventoryOperationLine, InventoryV1Stock,
    InventoryV1StockMovement,
)
from inventory.infrastructure.django.repositories import (
    DjangoIngredientRepository, DjangoStockMovementRepository,
    DjangoStockRepository, DjangoWarehouseRepository,
)
from inventory.infrastructure.django.unit_of_work import DjangoInventoryUnitOfWork
from inventory.models import Ingredient, Warehouse


class OperationInputError(ValueError):
    pass


def _atomic():
    return DjangoInventoryUnitOfWork().atomic()


def _document(business_id, operation_type, operation_id, *, lock=False):
    rows = InventoryOperation.objects.filter(
        business_id=business_id, operation_type=operation_type, pk=operation_id
    )
    if lock:
        rows = rows.select_for_update()
    row = rows.prefetch_related("lines__ingredient").first()
    if row is None:
        raise ResourceNotFound("Inventory operation was not found in this business.")
    return row


def _stock(business_id, warehouse, ingredient, *, create=False):
    if create:
        InventoryV1Stock.objects.get_or_create(
            business_id=business_id, warehouse=warehouse, ingredient=ingredient,
            defaults={"unit": ingredient.unit},
        )
    row = InventoryV1Stock.objects.select_for_update().filter(
        business_id=business_id, warehouse=warehouse, ingredient=ingredient,
        warehouse__business_id=business_id, ingredient__business_id=business_id,
    ).first()
    if row is None:
        raise OperationInputError("Stock position does not exist for this item and warehouse.")
    return row, stock_to_domain(row)


def _identity(document, line, operation_kind):
    return SourceIdentity(
        document.business_id, f"inventory_{document.operation_type}",
        document.pk, line.pk, operation_kind,
    )


def create_operation(*, business_id, actor_id, operation_type, warehouse_id,
                     destination_warehouse_id=None, reference="", reason="", notes="", lines):
    if operation_type not in InventoryOperation.Type.values:
        raise OperationInputError("Unsupported inventory operation type.")
    if not lines:
        raise OperationInputError("At least one item is required.")
    if len({line["ingredient_id"] for line in lines}) != len(lines):
        raise OperationInputError("Each item may appear only once per document.")
    with _atomic():
        warehouse = Warehouse.objects.filter(pk=warehouse_id, business_id=business_id).first()
        if warehouse is None:
            raise ResourceNotFound("Warehouse was not found in this business.")
        if not warehouse.is_active:
            raise OperationInputError("Inactive warehouses cannot be used.")
        destination = None
        if operation_type == InventoryOperation.Type.TRANSFER:
            destination = Warehouse.objects.filter(
                pk=destination_warehouse_id, business_id=business_id, is_active=True
            ).first()
            if destination is None or destination.pk == warehouse.pk:
                raise OperationInputError("Choose a distinct active destination warehouse in this business.")
        elif destination_warehouse_id is not None:
            raise OperationInputError("Destination is only valid for transfers.")
        document = InventoryOperation.objects.create(
            business_id=business_id, operation_type=operation_type,
            warehouse=warehouse, destination_warehouse=destination,
            reference=reference.strip(), reason=reason.strip(), notes=notes.strip(),
            created_by_id=actor_id,
        )
        for item in sorted(lines, key=lambda entry: entry["ingredient_id"]):
            ingredient = Ingredient.objects.select_for_update().filter(
                pk=item["ingredient_id"], business_id=business_id, is_active=True
            ).first()
            if ingredient is None:
                raise ResourceNotFound("An active item was not found in this business.")
            requested_type = item.get("material_type")
            actual_type = "compound" if ingredient.preparation_level == "semi_prepared" else "raw"
            if requested_type is not None and requested_type != actual_type:
                raise OperationInputError("Selected material type does not match the ingredient.")
            unit = Unit(item["unit"])
            quantity = Quantity(item["quantity"], unit).convert_to(Unit(ingredient.unit))
            is_stocktake = operation_type == InventoryOperation.Type.STOCKTAKE
            if not is_stocktake and quantity.amount <= 0:
                raise OperationInputError("Operation quantities must be positive.")
            snapshot = None
            snapshot_movement_id = None
            counted = None
            if is_stocktake:
                stock_row, _ = _stock(business_id, warehouse, ingredient, create=True)
                snapshot = stock_row.quantity
                counted_value = item.get("counted_quantity")
                counted = (Quantity(counted_value, unit).convert_to(Unit(ingredient.unit)).amount
                           if counted_value is not None else None)
                counted_cost = item.get("counted_unit_cost")
                latest = InventoryV1StockMovement.objects.filter(stock=stock_row).order_by("-pk").values_list("pk", flat=True).first()
                snapshot_movement_id = latest
            InventoryOperationLine.objects.create(
                operation=document, ingredient=ingredient, quantity=quantity.amount,
                unit=ingredient.unit, system_quantity=snapshot,
                counted_quantity=counted,
                counted_unit_cost=UnitCost(counted_cost).amount if is_stocktake and counted_cost is not None else None,
                counted_by_id=actor_id if counted is not None else None,
                counted_at=timezone.now() if counted is not None else None,
                snapshot_movement_id=snapshot_movement_id,
            )
        return document


def create_opening_stock(*, business_id, actor_id, warehouse_id, reference="", reason="", notes="", lines):
    """Atomically initialize never-used V1 stock positions and append their ledger entries."""
    if not lines:
        raise OperationInputError("At least one item is required.")
    if len({line["ingredient_id"] for line in lines}) != len(lines):
        raise OperationInputError("Each item may appear only once in an opening entry.")

    with _atomic():
        # This lock serializes opening submissions for a warehouse. Stock-row locks
        # also serialize against normal Inventory V1 movements for each item.
        warehouse = Warehouse.objects.select_for_update().filter(
            pk=warehouse_id, business_id=business_id
        ).first()
        if warehouse is None:
            raise ResourceNotFound("Warehouse was not found in this business.")
        if not warehouse.is_active:
            raise OperationInputError("Inactive warehouses cannot receive opening stock.")

        document = InventoryOperation.objects.create(
            business_id=business_id,
            operation_type=InventoryOperation.Type.OPENING_STOCK,
            status=InventoryOperation.Status.POSTED,
            warehouse=warehouse,
            reference=reference.strip(),
            reason=reason.strip(),
            notes=notes.strip(),
            created_by_id=actor_id,
            completed_by_id=actor_id,
            completed_at=timezone.now(),
        )
        for item in sorted(lines, key=lambda entry: entry["ingredient_id"]):
            ingredient = Ingredient.objects.select_for_update().filter(
                pk=item["ingredient_id"], business_id=business_id, is_active=True
            ).first()
            if ingredient is None:
                raise ResourceNotFound("An active item was not found in this business.")
            requested_type = item.get("material_type")
            actual_type = "compound" if ingredient.preparation_level == "semi_prepared" else "raw"
            if requested_type is not None and requested_type != actual_type:
                raise OperationInputError("Selected material type does not match the ingredient.")
            quantity = Quantity(item["quantity"], Unit(item["unit"])).convert_to(
                Unit(ingredient.unit)
            )
            unit_cost = UnitCost(item["unit_cost"])
            if quantity.amount <= 0:
                raise OperationInputError("Opening quantities must be positive.")

            line = InventoryOperationLine.objects.create(
                operation=document,
                ingredient=ingredient,
                quantity=quantity.amount,
                unit=ingredient.unit,
            )
            stock_row, stock = _stock(business_id, warehouse, ingredient, create=True)
            has_history = InventoryV1StockMovement.objects.filter(stock=stock_row).exists()
            if stock.quantity.amount != 0 or stock.average_cost.amount != 0 or has_history:
                raise OperationConflict(
                    f"{ingredient.name} already has a balance or movement history in this warehouse; opening stock can only initialize an unused position."
                )
            movement = stock.open_balance(
                quantity,
                unit_cost,
                _identity(document, line, "post"),
                warehouse_to_domain(warehouse),
                actor_id=actor_id,
                reason=reason.strip() or "Initial stock entry",
            )
            stock_to_orm(stock, row=stock_row).save()
            movement_to_orm(movement, stock_row).save(force_insert=True)
        return document


def list_operations(business_id, operation_type, page=1, page_size=20):
    rows = InventoryOperation.objects.filter(business_id=business_id, operation_type=operation_type)
    count = rows.count()
    return count, list(rows.prefetch_related("lines__ingredient").order_by("-pk")[(page-1)*page_size:page*page_size])


def get_operation(business_id, operation_type, operation_id):
    return _document(business_id, operation_type, operation_id)


def update_stocktake_counts(*, business_id, actor_id, operation_id, counts):
    with _atomic():
        document = _document(business_id, InventoryOperation.Type.STOCKTAKE, operation_id, lock=True)
        if document.status != InventoryOperation.Status.DRAFT:
            raise OperationConflict("Only a draft stocktake can be counted.")
        for line_id, values in counts.items():
            line = document.lines.filter(pk=line_id).first()
            if line is None:
                raise ResourceNotFound("Stocktake line was not found.")
            line.counted_quantity = Quantity(values["counted_quantity"], Unit(line.unit)).amount
            cost = values.get("counted_unit_cost")
            line.counted_unit_cost = UnitCost(cost).amount if cost is not None else None
            line.counted_by_id = actor_id
            line.counted_at = timezone.now()
            line.save(update_fields=("counted_quantity", "counted_unit_cost", "counted_by_id", "counted_at"))
        return _document(business_id, InventoryOperation.Type.STOCKTAKE, operation_id)


def _locked_document_lines(business_id, operation_type, operation_id):
    document = _document(business_id, operation_type, operation_id, lock=True)
    lines = list(document.lines.select_related("ingredient").order_by("ingredient_id").select_for_update())
    return document, lines


def post_issue(*, business_id, actor_id, operation_id):
    with _atomic():
        document, lines = _locked_document_lines(business_id, InventoryOperation.Type.ISSUE, operation_id)
        if document.status == InventoryOperation.Status.POSTED:
            return document
        if document.status != InventoryOperation.Status.DRAFT:
            raise OperationConflict("Only a draft issue can be posted.")
        warehouse = warehouse_to_domain(document.warehouse)
        for line in lines:
            if not line.ingredient.is_active:
                raise OperationInputError("Inactive items cannot be issued.")
            row, stock = _stock(business_id, document.warehouse, line.ingredient)
            movement = stock.issue(
                Quantity(line.quantity, Unit(line.unit)), _identity(document, line, "post"),
                warehouse, reason=document.reason or "Stock issue", actor_id=actor_id,
            )
            DjangoStockRepository().save(stock)
            movement_to_orm(movement, row).save(force_insert=True)
        document.status = InventoryOperation.Status.POSTED
        document.completed_by_id = actor_id
        document.completed_at = timezone.now()
        document.save(update_fields=("status", "completed_by_id", "completed_at"))
        return document


def reverse_issue(*, business_id, actor_id, operation_id):
    with _atomic():
        document, lines = _locked_document_lines(business_id, InventoryOperation.Type.ISSUE, operation_id)
        if document.status == InventoryOperation.Status.REVERSED:
            return document
        if document.status != InventoryOperation.Status.POSTED:
            raise OperationConflict("Only a posted issue can be reversed.")
        use_case = ReverseStockMovementUseCase(
            DjangoWarehouseRepository(), DjangoIngredientRepository(),
            DjangoStockRepository(), DjangoStockMovementRepository(),
            DjangoInventoryUnitOfWork(),
        )
        context = InventoryExecutionContext(business_id, actor_id)
        for line in lines:
            use_case.execute(
                ReverseStockMovementCommand(
                    target=OperationIdentityInput("inventory_issue", document.pk, line.pk, "post"),
                    source=OperationIdentityInput("inventory_issue", document.pk, line.pk, "reverse"),
                    reason=f"Issue reversal: {document.reason}".strip(),
                ), context,
            )
        document.status = InventoryOperation.Status.REVERSED
        document.completed_by_id = actor_id
        document.completed_at = timezone.now()
        document.save(update_fields=("status", "completed_by_id", "completed_at"))
        return document


def dispatch_transfer(*, business_id, actor_id, operation_id):
    with _atomic():
        document, lines = _locked_document_lines(business_id, InventoryOperation.Type.TRANSFER, operation_id)
        if document.status == InventoryOperation.Status.IN_TRANSIT:
            return document
        if document.status != InventoryOperation.Status.DRAFT:
            raise OperationConflict("Only a draft transfer can be dispatched.")
        warehouse = warehouse_to_domain(document.warehouse)
        for line in lines:
            if not line.ingredient.is_active:
                raise OperationInputError("Inactive items cannot be dispatched.")
            row, stock = _stock(business_id, document.warehouse, line.ingredient)
            line.transfer_unit_cost = stock.average_cost.amount
            movement = stock.transfer_out(
                Quantity(line.quantity, Unit(line.unit)), _identity(document, line, "dispatch"),
                warehouse, actor_id=actor_id,
            )
            DjangoStockRepository().save(stock)
            movement_to_orm(movement, row).save(force_insert=True)
            line.save(update_fields=("transfer_unit_cost",))
        document.status = InventoryOperation.Status.IN_TRANSIT
        document.completed_by_id = actor_id
        document.completed_at = timezone.now()
        document.save(update_fields=("status", "completed_by_id", "completed_at"))
        return document


def receive_transfer(*, business_id, actor_id, operation_id):
    with _atomic():
        document, lines = _locked_document_lines(business_id, InventoryOperation.Type.TRANSFER, operation_id)
        if document.status == InventoryOperation.Status.RECEIVED:
            return document
        if document.status != InventoryOperation.Status.IN_TRANSIT:
            raise OperationConflict("Only an in-transit transfer can be received.")
        destination = warehouse_to_domain(document.destination_warehouse)
        for line in lines:
            row, stock = _stock(business_id, document.destination_warehouse, line.ingredient, create=True)
            movement = stock.transfer_in(
                Quantity(line.quantity, Unit(line.unit)), UnitCost(line.transfer_unit_cost),
                _identity(document, line, "receive"), destination, actor_id=actor_id,
            )
            DjangoStockRepository().save(stock)
            movement_to_orm(movement, row).save(force_insert=True)
        document.status = InventoryOperation.Status.RECEIVED
        document.completed_by_id = actor_id
        document.completed_at = timezone.now()
        document.save(update_fields=("status", "completed_by_id", "completed_at"))
        return document


def approve_stocktake(*, business_id, actor_id, operation_id):
    with _atomic():
        document, lines = _locked_document_lines(business_id, InventoryOperation.Type.STOCKTAKE, operation_id)
        if document.status == InventoryOperation.Status.APPROVED:
            return document
        if document.status != InventoryOperation.Status.DRAFT or any(line.counted_quantity is None for line in lines):
            raise OperationConflict("A draft stocktake with all counts is required for approval.")
        warehouse = warehouse_to_domain(document.warehouse)
        warehouse.ensure_active()
        for line in lines:
            row, stock = _stock(business_id, document.warehouse, line.ingredient)
            latest_id = InventoryV1StockMovement.objects.filter(stock=row).order_by("-pk").values_list("pk", flat=True).first()
            if row.quantity != line.system_quantity or latest_id != line.snapshot_movement_id:
                raise OperationConflict("Stock changed after the count snapshot; cancel this draft and create a fresh stocktake before approval.")
            counted = Decimal(line.counted_quantity)
            snapshot = Decimal(line.system_quantity)
            delta = counted - snapshot
            if delta:
                from inventory.domain.enums.movement import MovementDirection
                unit_cost = None
                if delta > 0 and stock.average_cost.amount == 0:
                    if line.counted_unit_cost is None:
                        raise OperationInputError(
                            "A unit cost is required when a stocktake adds quantity to zero-cost stock."
                        )
                    unit_cost = UnitCost(line.counted_unit_cost)
                movement = stock.adjust(
                    Quantity(abs(delta), Unit(line.unit)),
                    MovementDirection.IN if delta > 0 else MovementDirection.OUT,
                    _identity(document, line, "approve"), warehouse,
                    reason=document.reason or "Physical stocktake variance", actor_id=actor_id,
                    unit_cost=unit_cost,
                )
                DjangoStockRepository().save(stock)
                movement_to_orm(movement, row).save(force_insert=True)
        document.status = InventoryOperation.Status.APPROVED
        document.completed_by_id = actor_id
        document.completed_at = timezone.now()
        document.save(update_fields=("status", "completed_by_id", "completed_at"))
        return document


def cancel_operation(*, business_id, operation_type, operation_id):
    with _atomic():
        document = _document(business_id, operation_type, operation_id, lock=True)
        if document.status != InventoryOperation.Status.DRAFT:
            raise OperationConflict("Only a draft operation can be cancelled.")
        document.status = InventoryOperation.Status.CANCELLED
        document.save(update_fields=("status",))
        return document


def movement_history(*, business_id, page=1, page_size=20, warehouse_id=None,
                     ingredient_id=None, material_type=None, movement_type=None, date_from=None, date_to=None,
                     reference=None, actor_id=None, search=None):
    rows = InventoryV1StockMovement.objects.filter(
        business_id=business_id, stock__business_id=business_id,
        stock__warehouse__business_id=business_id, stock__ingredient__business_id=business_id,
    ).select_related("stock__warehouse", "stock__ingredient")
    if warehouse_id: rows = rows.filter(stock__warehouse_id=warehouse_id)
    if ingredient_id: rows = rows.filter(stock__ingredient_id=ingredient_id)
    if material_type:
        rows = rows.filter(stock__ingredient__preparation_level=(
            "raw" if material_type == "raw" else "semi_prepared"
        ))
    if search:
        rows = rows.filter(stock__ingredient__name__icontains=search.strip())
    if movement_type: rows = rows.filter(movement_type=movement_type)
    if date_from: rows = rows.filter(created_at__date__gte=date_from)
    if date_to: rows = rows.filter(created_at__date__lte=date_to)
    if reference:
        operation_ids = InventoryOperation.objects.filter(
            business_id=business_id, reference__icontains=reference,
        ).values("pk")
        reference_filter = Q(
            source_type__in=("inventory_issue", "inventory_transfer", "inventory_stocktake", "inventory_opening_stock"),
            source_document_id__in=Subquery(operation_ids),
        )
        if reference.isdigit():
            reference_filter |= Q(source_document_id=int(reference))
        rows = rows.filter(reference_filter)
    if actor_id: rows = rows.filter(actor_id=actor_id)
    count = rows.count()
    return count, list(rows.order_by("-pk")[(page-1)*page_size:page*page_size])
