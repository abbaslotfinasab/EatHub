"""Order-to-Inventory V1 orchestration; all writes join the caller transaction."""

from decimal import Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from uuid import UUID, uuid5

from django.db import transaction
from django.db import IntegrityError
from django.db.models import Sum
from rest_framework.exceptions import ValidationError

from inventory.application.context import InventoryExecutionContext
from inventory.application.exceptions import InvalidApplicationInput, OperationConflict, ResourceNotFound
from inventory.application.use_cases.manage_reservations import ManageReservations
from inventory.domain.exceptions import InventoryDomainError
from inventory.domain.value_objects.quantity import Quantity
from inventory.domain.value_objects.unit import Unit
from inventory.infrastructure.django.models import (
    InventoryOperation,
    InventoryOperationLine,
    InventoryReservation,
    InventoryV1StockMovement,
)
from inventory.infrastructure.django.operations_service import OperationInputError, create_operation, post_issue
from inventory.infrastructure.django.reservation_repository import DjangoReservationRepository
from inventory.infrastructure.django.unit_of_work import DjangoInventoryUnitOfWork
from inventory.models import Ingredient, Recipe, Warehouse
from products.models import (
    MenuItem,
    Order,
    OrderInventoryConsumption,
    OrderInventoryConsumptionLine,
    OrderItemIngredientRequirement,
    OrderItemRecipeSnapshot,
)


_ORDER_KEY_NAMESPACE = UUID("90144542-95ef-4eef-a498-0e73f429725d")
_QUANTITY_QUANTUM = Decimal("0.000000000001")
_MAX_QUANTITY = Decimal("999999999999999999999999.999999999999")


def _reservation_use_case():
    return ManageReservations(DjangoReservationRepository(), DjangoInventoryUnitOfWork())


def _context(order: Order, actor_id: int) -> InventoryExecutionContext:
    return InventoryExecutionContext(order.business_id, actor_id)


def _inventory_call(call):
    try:
        return call()
    except ResourceNotFound as error:
        raise ValidationError(str(error)) from error
    except (OperationConflict, InvalidApplicationInput, InventoryDomainError, OperationInputError) as error:
        raise ValidationError({"inventory": str(error)}) from error


def _scaled_quantity(input_quantity: Decimal, order_quantity: int, output_quantity: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = 80
        raw = input_quantity * Decimal(order_quantity) / output_quantity
        try:
            normalized = raw.quantize(_QUANTITY_QUANTUM)
        except InvalidOperation as error:
            raise ValidationError("Recipe scaling exceeds supported inventory precision.") from error
    if normalized != raw or normalized <= 0 or normalized > _MAX_QUANTITY:
        raise ValidationError("Recipe scaling cannot be represented exactly in inventory units.")
    return normalized


class OrderInventoryService:
    """Coordinates immutable recipe snapshots, reservation holds and actual issues."""

    @staticmethod
    @transaction.atomic
    def confirm(*, order: Order, actor_id: int) -> None:
        items = list(order.items.select_for_update().order_by("pk"))
        if not items:
            raise ValidationError("An order needs at least one item before confirmation.")
        if OrderItemRecipeSnapshot.objects.filter(order_id=order.pk).exists():
            if OrderItemRecipeSnapshot.objects.filter(order_id=order.pk).count() != len(items):
                raise ValidationError("This order has an incomplete legacy recipe snapshot and needs review.")
            # A retry returns through the reservation idempotency key below.
            return

        defaults = list(
            Warehouse.objects.filter(
                business_id=order.business_id, is_active=True, is_default=True
            ).order_by("pk")
        )
        if len(defaults) != 1:
            raise ValidationError("Configure exactly one active default warehouse before confirming recipe-based orders.")
        warehouse = defaults[0]

        menu_items = {
            row.pk: row
            for row in MenuItem.objects.select_for_update().filter(
                business_id=order.business_id,
                pk__in=[item.menu_item_id for item in items if item.menu_item_id is not None],
            ).select_related("recipe").order_by("pk")
        }

        snapshots = []
        requirements = []
        reservation_by_ingredient: dict[int, tuple[Decimal, Unit]] = {}
        for item in items:
            menu_item = menu_items.get(item.menu_item_id)
            if menu_item is None or menu_item.business_id != order.business_id:
                raise ValidationError({"items": "Every order item must resolve to a menu item in this business."})
            recipe_id = menu_item.recipe_id
            if recipe_id is None:
                raise ValidationError({"items": f"Menu item '{item.menu_item_name}' has no usable recipe."})
            try:
                recipe = (
                    Recipe.objects.select_for_update()
                    .prefetch_related("inputs__ingredient", "outputs__ingredient")
                    .get(pk=recipe_id, business_id=order.business_id)
                )
            except Recipe.DoesNotExist as error:
                raise ValidationError({"items": "A linked recipe was not found in this business."}) from error
            if not recipe.is_active:
                raise ValidationError({"items": f"Recipe '{recipe.name}' is inactive."})
            primary_outputs = [line for line in recipe.outputs.all() if line.is_primary]
            if len(primary_outputs) != 1:
                raise ValidationError({"items": f"Recipe '{recipe.name}' must have one primary output."})
            primary = primary_outputs[0]
            if primary.ingredient.business_id != order.business_id or not primary.ingredient.is_active:
                raise ValidationError({"items": "The primary recipe output is not an active ingredient in this business."})
            if primary.unit != "pc" or primary.ingredient.unit != "pc":
                raise ValidationError({
                    "items": "Order quantity is a piece count; the linked recipe must declare its primary output in pc."
                })
            output_quantity = Decimal(primary.quantity)
            if output_quantity <= 0:
                raise ValidationError("The recipe primary output quantity must be positive.")

            snapshot = OrderItemRecipeSnapshot.objects.create(
                business_id=order.business_id,
                order=order,
                order_item=item,
                recipe=recipe,
                recipe_output_ingredient=primary.ingredient,
                recipe_updated_at=recipe.updated_at,
                output_quantity=output_quantity,
                output_unit="pc",
            )
            snapshots.append(snapshot)
            input_rows = list(recipe.inputs.select_related("ingredient").order_by("pk"))
            if not input_rows:
                raise ValidationError({"items": f"Recipe '{recipe.name}' has no inventory inputs."})
            for input_line in input_rows:
                ingredient = input_line.ingredient
                if ingredient.business_id != order.business_id or not ingredient.is_active:
                    raise ValidationError({"items": "A recipe input is inactive or outside this business."})
                try:
                    canonical_unit = Unit(ingredient.unit)
                    input_quantity = Quantity(input_line.quantity, Unit(input_line.unit)).convert_to(canonical_unit)
                except (InventoryDomainError, TypeError, ValueError) as error:
                    raise ValidationError({"items": "A recipe input has an invalid or incompatible unit."}) from error
                required = _scaled_quantity(input_quantity.amount, item.quantity, output_quantity)
                requirement = OrderItemIngredientRequirement.objects.create(
                    snapshot=snapshot,
                    ingredient=ingredient,
                    recipe_input_id=input_line.pk,
                    standard_quantity=required,
                    unit=canonical_unit.value,
                )
                requirements.append(requirement)
                previous, previous_unit = reservation_by_ingredient.get(
                    ingredient.pk, (Decimal("0"), canonical_unit)
                )
                if previous_unit is not canonical_unit:
                    raise ValidationError("A recipe uses incompatible canonical units for one ingredient.")
                with localcontext() as ctx:
                    ctx.prec = 80
                    reservation_by_ingredient[ingredient.pk] = (previous + required, canonical_unit)

        if not requirements:
            raise ValidationError("No inventory requirements could be resolved for this order.")
        use_case = _reservation_use_case()
        _inventory_call(lambda: use_case.create_for_order(
            _context(order, actor_id),
            warehouse_id=warehouse.pk,
            order_id=order.pk,
            reason=f"Order {order.pk} confirmation",
            idempotency_key=uuid5(_ORDER_KEY_NAMESPACE, f"reserve:{order.business_id}:{order.pk}"),
            lines=[
                {"ingredient_id": ingredient_id, "quantity": str(quantity), "unit": unit.value}
                for ingredient_id, (quantity, unit) in sorted(reservation_by_ingredient.items())
            ],
        ))

    @staticmethod
    @transaction.atomic
    def release_remaining(*, order: Order, actor_id: int, reason: str) -> None:
        active = InventoryReservation.objects.select_for_update().filter(
            business_id=order.business_id,
            warehouse__business_id=order.business_id,
            source_type="order",
            source_id=order.pk,
            status=InventoryReservation.Status.ACTIVE,
        ).first()
        if active is None:
            return
        _inventory_call(lambda: _reservation_use_case().release(
            _context(order, actor_id),
            active.pk,
            uuid5(_ORDER_KEY_NAMESPACE, f"release:{active.pk}"),
            reason,
        ))

    @staticmethod
    @transaction.atomic
    def record_consumption(*, business_id: int, order_id: int, actor_id: int,
                           idempotency_key: UUID, lines: list[dict]) -> OrderInventoryConsumption:
        try:
            order = Order.objects.select_for_update().get(pk=order_id, business_id=business_id)
        except Order.DoesNotExist as error:
            raise ResourceNotFound("Order was not found in this business.") from error
        if order.status != Order.Status.PREPARING:
            raise OperationConflict("Actual consumption can be recorded only while an order is preparing.")
        if not lines:
            raise ValidationError({"lines": "At least one actual-consumption line is required."})

        requirements = {
            row.pk: row
            for row in OrderItemIngredientRequirement.objects.filter(
                snapshot__business_id=business_id,
                snapshot__order_id=order.pk,
                snapshot__order__business_id=business_id,
            ).select_related("ingredient", "snapshot__order_item").order_by("pk")
        }
        if any(
            requirement.ingredient.business_id != business_id
            or requirement.snapshot.order_item.order_id != order.pk
            for requirement in requirements.values()
        ):
            raise OperationConflict("Persisted recipe requirements do not match this business and order.")
        if not requirements:
            raise ValidationError("This order has no immutable inventory requirement snapshot.")

        normalized = []
        seen = set()
        actual_by_ingredient: dict[int, tuple[Decimal, Unit]] = {}
        for raw in lines:
            requirement_id = raw.get("requirement_id")
            if requirement_id in seen:
                raise ValidationError({"lines": "A requirement can appear only once per consumption request."})
            seen.add(requirement_id)
            requirement = requirements.get(requirement_id)
            if requirement is None:
                raise ResourceNotFound("A requirement was not found in this order and business.")
            try:
                unit = Unit(raw.get("unit", requirement.unit))
                amount = Quantity(raw.get("quantity"), unit).convert_to(Unit(requirement.unit)).amount
            except (InventoryDomainError, TypeError, ValueError) as error:
                raise ValidationError({"lines": "Actual quantity is invalid or uses an incompatible unit."}) from error
            if amount < 0:
                raise ValidationError({"lines": "Actual quantity cannot be negative."})
            normalized.append((requirement, amount, Unit(requirement.unit)))
            prior = actual_by_ingredient.get(requirement.ingredient_id, (Decimal("0"), Unit(requirement.unit)))
            if prior[1] is not Unit(requirement.unit):
                raise ValidationError("Persisted requirements use incompatible units for one ingredient.")
            with localcontext() as ctx:
                ctx.prec = 80
                actual_by_ingredient[requirement.ingredient_id] = (prior[0] + amount, prior[1])

        payload = {
            "order_id": order.pk,
            "lines": sorted([
                {"requirement_id": row.pk, "quantity": format(amount, "f"), "unit": unit.value}
                for row, amount, unit in normalized
            ], key=lambda item: item["requirement_id"]),
        }
        fingerprint = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        existing = OrderInventoryConsumption.objects.select_for_update().filter(
            business_id=business_id, idempotency_key=idempotency_key
        ).first()
        if existing is not None:
            if existing.order_id != order.pk or existing.payload_fingerprint != fingerprint:
                raise OperationConflict("This consumption idempotency key was used with different data.")
            return existing

        previous = {}
        for row in OrderInventoryConsumptionLine.objects.filter(
            consumption__business_id=business_id,
            consumption__order_id=order.pk,
            requirement_id__in=requirements,
        ).values("requirement_id").annotate(total=Sum("actual_quantity")):
            previous[row["requirement_id"]] = Decimal(row["total"] or 0)
        for requirement, amount, _unit in normalized:
            if previous.get(requirement.pk, Decimal("0")) + amount > requirement.standard_quantity:
                raise OperationConflict("Actual consumption cannot exceed the confirmed reserved requirement.")

        reservation = InventoryReservation.objects.select_for_update().filter(
            business_id=business_id,
            warehouse__business_id=business_id,
            source_type="order",
            source_id=order.pk,
            status=InventoryReservation.Status.ACTIVE,
        ).first()
        positive_actual = {key: value for key, value in actual_by_ingredient.items() if value[0] > 0}
        old_reservation_lines = []
        if positive_actual:
            if reservation is None:
                raise OperationConflict("No active reservation remains for this order.")
            old_reservation_lines = list(reservation.lines.select_related("ingredient").order_by("ingredient_id"))
            reserved = {row.ingredient_id: (Decimal(row.quantity), Unit(row.unit)) for row in old_reservation_lines}
            remaining = []
            for ingredient_id, (used, unit) in sorted(actual_by_ingredient.items()):
                current, reserved_unit = reserved.get(ingredient_id, (Decimal("0"), unit))
                if reserved_unit is not unit or used > current:
                    raise OperationConflict("Actual consumption exceeds the remaining reserved quantity.")
                remainder = current - used
                if remainder > 0:
                    remaining.append({"ingredient_id": ingredient_id, "quantity": str(remainder), "unit": unit.value})
            for ingredient_id, (current, unit) in reserved.items():
                if ingredient_id not in actual_by_ingredient and current > 0:
                    remaining.append({"ingredient_id": ingredient_id, "quantity": str(current), "unit": unit.value})

        try:
            with transaction.atomic():
                event = OrderInventoryConsumption.objects.create(
                    business_id=business_id,
                    order=order,
                    idempotency_key=idempotency_key,
                    payload_fingerprint=fingerprint,
                    actor_id=actor_id,
                )
        except IntegrityError as error:
            raise OperationConflict("This consumption idempotency key is already in use.") from error
        event_lines = [OrderInventoryConsumptionLine.objects.create(
            consumption=event,
            requirement=requirement,
            actual_quantity=amount,
            unit=unit.value,
        ) for requirement, amount, unit in normalized]

        if positive_actual:
            use_case = _reservation_use_case()
            _inventory_call(lambda: use_case.release(
                _context(order, actor_id),
                reservation.pk,
                uuid5(_ORDER_KEY_NAMESPACE, f"consume-release:{event.pk}"),
                f"Replaced by consumption {event.pk}",
            ))
            if remaining:
                _inventory_call(lambda: use_case.create_for_order(
                    _context(order, actor_id),
                    warehouse_id=reservation.warehouse_id,
                    order_id=order.pk,
                    reason=f"Order {order.pk} remaining requirement after consumption {event.pk}",
                    idempotency_key=uuid5(_ORDER_KEY_NAMESPACE, f"consume-reserve:{event.pk}"),
                    lines=remaining,
                ))

            operation = _inventory_call(lambda: create_operation(
                business_id=business_id,
                actor_id=actor_id,
                operation_type=InventoryOperation.Type.ISSUE,
                warehouse_id=reservation.warehouse_id,
                reference=f"Order {order.pk}",
                reason=f"Actual consumption for order {order.pk}",
                notes=f"OrderInventoryConsumption:{event.pk}",
                lines=[
                    {
                        "ingredient_id": ingredient_id,
                        "quantity": str(amount),
                        "unit": unit.value,
                    }
                    for ingredient_id, (amount, unit) in sorted(positive_actual.items())
                ],
            ))
            _inventory_call(lambda: post_issue(business_id=business_id, actor_id=actor_id, operation_id=operation.pk))
            event.inventory_operation = operation
            event.save(update_fields=("inventory_operation", "updated_at"))
            movement_by_ingredient = {}
            for operation_line in InventoryOperationLine.objects.filter(
                operation=operation
            ).order_by("ingredient_id"):
                movement_by_ingredient[operation_line.ingredient_id] = InventoryV1StockMovement.objects.get(
                    business_id=business_id,
                    source_type="inventory_issue",
                    source_document_id=operation.pk,
                    source_line_id=operation_line.pk,
                    operation_kind="post",
                )
            for line in event_lines:
                if line.actual_quantity > 0:
                    line.inventory_movement = movement_by_ingredient[line.requirement.ingredient_id]
                    line.save(update_fields=("inventory_movement",))
        return event

    @staticmethod
    def ensure_consumption_complete(order: Order) -> None:
        requirements = set(
            OrderItemIngredientRequirement.objects.filter(
                snapshot__business_id=order.business_id, snapshot__order_id=order.pk
            ).values_list("pk", flat=True)
        )
        if not requirements:
            if not order.items.exists():
                # Legacy wallet-only tests/data can contain an empty order row;
                # it has no item requirement that can be estimated or deducted.
                return
            raise ValidationError("The order has no immutable recipe requirement snapshot.")
        recorded = set(
            OrderInventoryConsumptionLine.objects.filter(
                consumption__business_id=order.business_id,
                consumption__order_id=order.pk,
                requirement_id__in=requirements,
            ).values_list("requirement_id", flat=True)
        )
        if recorded != requirements:
            raise ValidationError("Record actual usage for every recipe requirement before marking the order ready.")

