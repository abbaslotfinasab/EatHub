from decimal import Decimal

from django.db import IntegrityError, connection, transaction
from django.db.models import Sum
from django.utils import timezone

from inventory.application.dto.reservation import (
    ReservationDTO,
    ReservationLineDTO,
    StockAvailabilityDTO,
)
from inventory.application.exceptions import OperationConflict, ResourceNotFound
from inventory.domain.entities.reservation import ReservationRequest
from inventory.domain.enums.reservation import ReservationStatus
from inventory.domain.value_objects.quantity import Quantity
from inventory.domain.value_objects.unit import Unit
from inventory.infrastructure.django.models import (
    InventoryReservation,
    InventoryReservationLine,
    InventoryV1Stock,
)
from inventory.infrastructure.django.mappers import ingredient_to_domain, warehouse_to_domain
from inventory.models import Ingredient, Warehouse


class ReservationPersistenceError(RuntimeError):
    """Persisted reservation data violates tenant or canonical-unit invariants."""


class DjangoReservationRepository:
    """Business-scoped reservation persistence and stock-row serialization."""

    @staticmethod
    def order_source_is_active(business_id, order_id):
        # Imported at the infrastructure boundary to keep Inventory's domain
        # and application layers independent from the Products ORM.
        from products.models import Order

        return Order.objects.filter(
            pk=order_id,
            business_id=business_id,
            status__in=(Order.Status.CONFIRMED, Order.Status.PREPARING),
        ).exists()

    @staticmethod
    def order_reservation_matches(business_id, order_id, lines):
        from products.models import (
            OrderInventoryConsumptionLine,
            OrderItemIngredientRequirement,
        )

        expected = {}
        requirements = OrderItemIngredientRequirement.objects.filter(
            snapshot__business_id=business_id,
            snapshot__order_id=order_id,
            snapshot__order__business_id=business_id,
            ingredient__business_id=business_id,
        ).values_list("pk", "ingredient_id", "standard_quantity", "unit")
        requirement_ids = set()
        for requirement_id, ingredient_id, quantity, unit in requirements:
            requirement_ids.add(requirement_id)
            previous, previous_unit = expected.get(ingredient_id, (Decimal("0"), unit))
            if previous_unit != unit:
                return False
            expected[ingredient_id] = (previous + Decimal(quantity), unit)
        if not expected:
            return False

        for line in OrderInventoryConsumptionLine.objects.filter(
            consumption__business_id=business_id,
            consumption__order_id=order_id,
            requirement_id__in=requirement_ids,
        ).select_related("requirement"):
            ingredient_id = line.requirement.ingredient_id
            current, unit = expected.get(ingredient_id, (Decimal("0"), line.unit))
            if unit != line.unit:
                return False
            expected[ingredient_id] = (current - Decimal(line.actual_quantity), unit)

        remaining = {key: value for key, value in expected.items() if value[0] > 0}
        provided = {}
        for line in lines:
            if line.ingredient_id in provided:
                return False
            provided[line.ingredient_id] = (line.quantity.amount, line.quantity.unit.value)
        return provided == {key: (value[0], value[1]) for key, value in remaining.items()}

    def lock_scope(self, business_id, warehouse_id, ingredient_ids):
        warehouse_rows = Warehouse.objects.filter(pk=warehouse_id, business_id=business_id)
        if connection.features.has_select_for_update:
            warehouse_rows = warehouse_rows.select_for_update(of=("self",))
        warehouse_row = warehouse_rows.first()

        ingredient_rows = Ingredient.objects.filter(
            business_id=business_id, pk__in=ingredient_ids
        ).order_by("pk")
        if connection.features.has_select_for_update:
            ingredient_rows = ingredient_rows.select_for_update(of=("self",))
        ingredients = {
            row.pk: ingredient_to_domain(row)
            for row in ingredient_rows
        }
        return (
            warehouse_to_domain(warehouse_row) if warehouse_row is not None else None,
            ingredients,
        )

    def get_by_idempotency_key(self, business_id, key, *, lock=False):
        rows = InventoryReservation.objects.filter(
            business_id=business_id, idempotency_key=key
        )
        if lock:
            rows = rows.select_for_update()
        row = rows.select_related("warehouse").prefetch_related("lines__ingredient").first()
        return self._dto(row) if row is not None else None

    def get_for_business(self, business_id, reservation_id, *, lock=False):
        rows = InventoryReservation.objects.filter(
            business_id=business_id, pk=reservation_id,
            warehouse__business_id=business_id,
        )
        if lock:
            rows = rows.select_for_update()
        row = rows.select_related("warehouse").prefetch_related("lines__ingredient").first()
        return self._dto(row) if row is not None else None

    def lock_stock_positions(self, business_id, warehouse_id, ingredient_ids):
        rows = InventoryV1Stock.objects.filter(
            business_id=business_id,
            warehouse_id=warehouse_id,
            ingredient_id__in=ingredient_ids,
            warehouse__business_id=business_id,
            ingredient__business_id=business_id,
        ).select_related("ingredient", "warehouse").order_by("warehouse_id", "ingredient_id")
        if connection.in_atomic_block:
            rows = rows.select_for_update(of=("self",))
        positions = {ingredient_id: None for ingredient_id in ingredient_ids}
        for row in rows:
            if row.unit != row.ingredient.unit:
                raise ReservationPersistenceError("Stock projection unit differs from the ingredient canonical unit.")
            positions[row.ingredient_id] = Quantity(row.quantity, Unit(row.unit))
        return positions

    def get_active_reserved(self, business_id, warehouse_id, ingredient_ids):
        grouped = (
            InventoryReservationLine.objects.filter(
                reservation__business_id=business_id,
                reservation__warehouse_id=warehouse_id,
                reservation__warehouse__business_id=business_id,
                reservation__status=InventoryReservation.Status.ACTIVE,
                ingredient_id__in=ingredient_ids,
                ingredient__business_id=business_id,
            )
            .values("ingredient_id", "unit")
            .annotate(total=Sum("quantity"))
        )
        ingredients = Ingredient.objects.filter(
            business_id=business_id, pk__in=ingredient_ids
        ).only("id", "unit").in_bulk(ingredient_ids)
        result = {}
        for row in grouped:
            ingredient = ingredients.get(row["ingredient_id"])
            if ingredient is None or ingredient.unit != row["unit"]:
                raise ReservationPersistenceError("Persisted reservation line has an invalid tenant or canonical unit.")
            if row["ingredient_id"] in result:
                raise ReservationPersistenceError("Persisted reservation lines use multiple units for one ingredient.")
            result[row["ingredient_id"]] = Quantity(row["total"], Unit(row["unit"]))
        return result

    def create(self, request: ReservationRequest, fingerprint: str, actor_id: int) -> ReservationDTO:
        try:
            # Keep a savepoint so a unique-key race can be translated without
            # marking the caller's outer transaction as broken.
            with transaction.atomic():
                header = InventoryReservation.objects.create(
                    business_id=request.business_id,
                    warehouse_id=request.warehouse_id,
                    source_type=request.source_type,
                    source_id=request.source_id,
                    reason=request.reason,
                    status=InventoryReservation.Status.ACTIVE,
                    idempotency_key=request.idempotency_key,
                    payload_fingerprint=fingerprint,
                    created_by_id=actor_id,
                )
                InventoryReservationLine.objects.bulk_create([
                    InventoryReservationLine(
                        reservation=header,
                        ingredient_id=line.ingredient_id,
                        source_line_id=line.source_line_id,
                        quantity=line.quantity.amount,
                        unit=line.quantity.unit.value,
                    )
                    for line in request.lines
                ])
            return self.get_for_business(request.business_id, header.pk)
        except IntegrityError as error:
            raise OperationConflict(
                "A reservation conflicts with an existing idempotency key or active source."
            ) from error

    def release(self, business_id, reservation_id, actor_id, idempotency_key, reason):
        header = InventoryReservation.objects.filter(
            business_id=business_id, pk=reservation_id,
            warehouse__business_id=business_id,
        ).select_for_update().first()
        if header is None:
            raise ResourceNotFound("Reservation was not found in this Business.")
        if header.status == InventoryReservation.Status.RELEASED:
            if (
                header.release_idempotency_key == idempotency_key
                and header.release_reason == reason
            ):
                return self._dto(
                    InventoryReservation.objects.select_related("warehouse")
                    .prefetch_related("lines__ingredient").get(pk=header.pk)
                )
            raise OperationConflict("This reservation has already been released.")

        ingredient_ids = list(
            header.lines.order_by("ingredient_id").values_list("ingredient_id", flat=True)
        )
        # Lock existing projection rows in the same order as reservation creation.
        # A missing row is safe here because release only lowers reserved quantity.
        list(self.lock_stock_positions(business_id, header.warehouse_id, ingredient_ids).items())
        try:
            with transaction.atomic():
                header.status = InventoryReservation.Status.RELEASED
                header.released_by_id = actor_id
                header.released_at = timezone.now()
                header.release_idempotency_key = idempotency_key
                header.release_reason = reason
                header.save(update_fields=(
                    "status", "released_by_id", "released_at", "release_idempotency_key",
                    "release_reason", "updated_at",
                ))
        except IntegrityError as error:
            raise OperationConflict("This release idempotency key is already in use.") from error
        return self._dto(
            InventoryReservation.objects.select_related("warehouse")
            .prefetch_related("lines__ingredient").get(pk=header.pk)
        )

    def list_for_business(self, business_id, *, source_type, source_id, status, page, page_size):
        rows = InventoryReservation.objects.filter(
            business_id=business_id,
            warehouse__business_id=business_id,
        )
        if source_type:
            rows = rows.filter(source_type=source_type)
        if source_id is not None:
            rows = rows.filter(source_id=source_id)
        if status:
            rows = rows.filter(status=status)
        count = rows.count()
        page_rows = rows.select_related("warehouse").prefetch_related("lines__ingredient").order_by("-created_at", "-pk")[(page - 1) * page_size:page * page_size]
        return count, [self._dto(row) for row in page_rows]

    def availability(self, business_id, warehouse_id, ingredient_id):
        warehouse = Warehouse.objects.filter(
            pk=warehouse_id, business_id=business_id
        ).first()
        ingredient = Ingredient.objects.filter(
            pk=ingredient_id, business_id=business_id
        ).first()
        if warehouse is None or ingredient is None:
            return None
        physical = self.lock_stock_positions(
            business_id, warehouse_id, [ingredient_id]
        )[ingredient_id]
        unit = Unit(ingredient.unit)
        physical_amount = physical.amount if physical is not None else Decimal("0")
        reserved = self.get_active_reserved(business_id, warehouse_id, [ingredient_id]).get(
            ingredient_id, Quantity.zero(unit)
        )
        if reserved.unit is not unit:
            raise ReservationPersistenceError("Persisted reservation unit differs from the ingredient canonical unit.")
        available = physical_amount - reserved.amount
        if available < 0:
            raise OperationConflict("Active reservations exceed physical stock; availability requires reconciliation.")
        return StockAvailabilityDTO(
            business_id=business_id,
            warehouse_id=warehouse_id,
            ingredient_id=ingredient_id,
            ingredient_name=ingredient.name,
            physical_quantity=physical_amount,
            reserved_quantity=reserved.amount,
            available_quantity=available,
            unit=unit,
        )

    @staticmethod
    def _dto(row) -> ReservationDTO:
        if row is None:
            raise ResourceNotFound("Reservation was not found in this Business.")
        if row.warehouse.business_id != row.business_id:
            raise ReservationPersistenceError("Persisted reservation warehouse belongs to another Business.")
        lines = []
        for line in row.lines.all().order_by("pk"):
            if line.ingredient.business_id != row.business_id:
                raise ReservationPersistenceError("Persisted reservation ingredient belongs to another Business.")
            if line.unit != line.ingredient.unit:
                raise ReservationPersistenceError("Persisted reservation line unit differs from the ingredient canonical unit.")
            lines.append(ReservationLineDTO(
                id=line.pk,
                ingredient_id=line.ingredient_id,
                ingredient_name=line.ingredient.name,
                source_line_id=line.source_line_id,
                quantity=line.quantity,
                unit=Unit(line.unit),
            ))
        return ReservationDTO(
            id=row.pk,
            business_id=row.business_id,
            warehouse_id=row.warehouse_id,
            warehouse_name=row.warehouse.name,
            source_type=row.source_type,
            source_id=row.source_id,
            reason=row.reason,
            status=ReservationStatus(row.status),
            idempotency_key=str(row.idempotency_key),
            payload_fingerprint=row.payload_fingerprint,
            created_by_id=row.created_by_id,
            released_by_id=row.released_by_id,
            released_at=row.released_at,
            release_reason=row.release_reason,
            created_at=row.created_at,
            updated_at=row.updated_at,
            lines=tuple(lines),
        )
