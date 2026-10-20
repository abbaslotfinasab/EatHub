from decimal import Decimal, InvalidOperation, localcontext

from inventory.domain.entities.ingredient import Ingredient
from inventory.domain.entities.stock import Stock
from inventory.domain.entities.stock_movement import StockMovement
from inventory.domain.entities.warehouse import Warehouse
from inventory.domain.enums.ingredient import IngredientPreparationLevel
from inventory.domain.enums.movement import MovementDirection, MovementType
from inventory.domain.exceptions import TenantMismatch
from inventory.domain.value_objects.quantity import Quantity
from inventory.domain.value_objects.source_identity import SourceIdentity
from inventory.domain.value_objects.stock_key import StockKey
from inventory.domain.value_objects.unit import Unit
from inventory.domain.value_objects.unit_cost import UnitCost
from inventory.infrastructure.django.models import (
    InventoryV1Stock,
    InventoryV1StockMovement,
)


class PersistenceMappingError(ValueError):
    """A valid Domain value cannot be represented losslessly by V1 columns."""


def _exact_decimal(value: Decimal, *, max_digits: int, decimal_places: int, field: str) -> Decimal:
    quantum = Decimal(1).scaleb(-decimal_places)
    try:
        with localcontext() as context:
            context.prec = max(80, len(value.as_tuple().digits) + decimal_places + 2)
            quantized = value.quantize(quantum)
    except InvalidOperation as error:
        raise PersistenceMappingError(f"{field} exceeds its persistence precision.") from error
    if quantized != value:
        raise PersistenceMappingError(f"{field} would lose Decimal precision.")
    integer_digits = max(value.copy_abs().adjusted() + 1, 1) if value else 1
    if integer_digits > max_digits - decimal_places:
        raise PersistenceMappingError(f"{field} exceeds its persistence range.")
    return value


def _source_text(value: str, field: str) -> str:
    if len(value) > 255:
        raise PersistenceMappingError(f"{field} exceeds 255 characters.")
    return value


def ingredient_to_domain(row) -> Ingredient:
    return Ingredient(
        id=row.pk,
        business_id=row.business_id,
        name=row.name,
        canonical_unit=Unit(row.unit),
        preparation_level=IngredientPreparationLevel(row.preparation_level),
        is_active=row.is_active,
    )


def warehouse_to_domain(row) -> Warehouse:
    return Warehouse(
        id=row.pk,
        business_id=row.business_id,
        name=row.name,
        code=row.code,
        is_active=row.is_active,
        is_default=row.is_default,
    )


def stock_to_domain(row) -> Stock:
    warehouse = warehouse_to_domain(row.warehouse)
    ingredient = ingredient_to_domain(row.ingredient)
    if not (row.business_id == warehouse.business_id == ingredient.business_id):
        raise TenantMismatch("Persisted Stock references cross Business ownership.")
    unit = ingredient.canonical_unit
    if Unit(row.unit) is not unit:
        raise PersistenceMappingError(
            "Persisted Stock unit differs from the Ingredient canonical unit."
        )
    return Stock.reconstitute(
        warehouse,
        ingredient,
        Quantity(row.quantity, unit),
        UnitCost(row.average_cost),
        reorder_level=(
            Quantity(row.reorder_level, unit) if row.reorder_level is not None else None
        ),
        reorder_quantity=(
            Quantity(row.reorder_quantity, unit)
            if row.reorder_quantity is not None
            else None
        ),
    )


def stock_to_orm(stock: Stock, row: InventoryV1Stock | None = None) -> InventoryV1Stock:
    quantity = _exact_decimal(
        stock.quantity.amount, max_digits=36, decimal_places=12, field="Stock.quantity"
    )
    average_cost = _exact_decimal(
        stock.average_cost.amount,
        max_digits=70,
        decimal_places=48,
        field="Stock.average_cost",
    )
    reorder_level = _exact_decimal(
        stock.reorder_level.amount,
        max_digits=36,
        decimal_places=12,
        field="Stock.reorder_level",
    )
    reorder_quantity = _exact_decimal(
        stock.reorder_quantity.amount,
        max_digits=36,
        decimal_places=12,
        field="Stock.reorder_quantity",
    )
    row = row or InventoryV1Stock()
    row.business_id = stock.key.business_id
    row.warehouse_id = stock.key.warehouse_id
    row.ingredient_id = stock.key.ingredient_id
    row.unit = stock.unit.value
    row.quantity = quantity
    row.average_cost = average_cost
    row.reorder_level = reorder_level
    row.reorder_quantity = reorder_quantity
    return row


def movement_to_domain(row) -> StockMovement:
    stock = row.stock
    if not (
        row.business_id
        == stock.business_id
        == stock.warehouse.business_id
        == stock.ingredient.business_id
    ):
        raise TenantMismatch("Persisted StockMovement references cross Business ownership.")
    projection = stock_to_domain(stock)
    unit = Unit(row.unit)
    if unit is not projection.unit:
        raise PersistenceMappingError(
            "Persisted StockMovement unit differs from the Stock canonical unit."
        )
    source = SourceIdentity(
        row.business_id,
        row.source_type,
        row.source_document_id,
        row.source_line_id,
        row.operation_kind,
    )
    reverses = (
        SourceIdentity(
            row.business_id,
            row.reverses_source_type,
            row.reverses_source_document_id,
            row.reverses_source_line_id,
            row.reverses_operation_kind,
        )
        if row.reverses_source_type is not None
        else None
    )
    return StockMovement.reconstitute(
        stock_key=StockKey(row.business_id, stock.warehouse_id, stock.ingredient_id),
        movement_type=MovementType(row.movement_type),
        direction=MovementDirection(row.direction),
        quantity=Quantity(row.quantity, unit),
        unit_cost=UnitCost(row.unit_cost),
        source_identity=source,
        balance_after=Quantity(row.balance_after, unit),
        average_cost_before=UnitCost(row.average_cost_before),
        reason=row.reason,
        actor_id=row.actor_id,
        reverses=reverses,
        occurred_at=row.occurred_at,
    )


def movement_to_orm(
    movement: StockMovement,
    stock_row: InventoryV1Stock,
) -> InventoryV1StockMovement:
    key = movement.stock_key
    if (
        stock_row.business_id != key.business_id
        or stock_row.warehouse_id != key.warehouse_id
        or stock_row.ingredient_id != key.ingredient_id
        or movement.source_identity.business_id != key.business_id
    ):
        raise TenantMismatch("Movement and persisted Stock must share a Business and key.")
    projection = stock_to_domain(stock_row)
    if movement.quantity.unit is not projection.unit:
        raise PersistenceMappingError(
            "StockMovement unit differs from the Stock canonical unit."
        )
    source = movement.source_identity
    reverses = movement.reverses
    quantity = _exact_decimal(
        movement.quantity.amount,
        max_digits=36,
        decimal_places=12,
        field="StockMovement.quantity",
    )
    balance_after = _exact_decimal(
        movement.balance_after.amount,
        max_digits=36,
        decimal_places=12,
        field="StockMovement.balance_after",
    )
    unit_cost = _exact_decimal(
        movement.unit_cost.amount,
        max_digits=70,
        decimal_places=48,
        field="StockMovement.unit_cost",
    )
    average_cost_before = _exact_decimal(
        movement.average_cost_before.amount,
        max_digits=70,
        decimal_places=48,
        field="StockMovement.average_cost_before",
    )
    return InventoryV1StockMovement(
        business_id=key.business_id,
        stock=stock_row,
        movement_type=movement.movement_type.value,
        direction=movement.direction.value,
        quantity=quantity,
        unit=movement.quantity.unit.value,
        unit_cost=unit_cost,
        balance_after=balance_after,
        average_cost_before=average_cost_before,
        source_type=_source_text(source.source_type, "SourceIdentity.source_type"),
        source_document_id=source.source_document_id,
        source_line_id=source.source_line_id,
        operation_kind=_source_text(source.operation_kind, "SourceIdentity.operation_kind"),
        actor_id=movement.actor_id,
        reason=movement.reason,
        reverses_source_type=(
            _source_text(reverses.source_type, "Reversal source_type")
            if reverses is not None
            else None
        ),
        reverses_source_document_id=(
            reverses.source_document_id if reverses is not None else None
        ),
        reverses_source_line_id=(reverses.source_line_id if reverses is not None else None),
        reverses_operation_kind=(
            _source_text(reverses.operation_kind, "Reversal operation_kind")
            if reverses is not None
            else None
        ),
        occurred_at=movement.occurred_at,
    )
