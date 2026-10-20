from inventory.application.context import InventoryExecutionContext
from inventory.application.dto.stock_operation import StockOperationResult
from inventory.application.exceptions import InvalidApplicationContext
from inventory.domain.entities.ingredient import Ingredient
from inventory.domain.entities.stock import Stock
from inventory.domain.entities.stock_movement import StockMovement
from inventory.domain.entities.warehouse import Warehouse
from inventory.domain.exceptions import TenantMismatch


def require_context(value: InventoryExecutionContext) -> InventoryExecutionContext:
    if not isinstance(value, InventoryExecutionContext):
        raise InvalidApplicationContext("A trusted Inventory execution context is required.")
    return value


def require_actor(context: InventoryExecutionContext) -> int:
    if context.actor_id is None:
        raise InvalidApplicationContext("This operation requires a trusted actor ID.")
    return context.actor_id


def validate_warehouse(warehouse: Warehouse, business_id: int, warehouse_id: int) -> None:
    if warehouse.business_id != business_id or warehouse.id != warehouse_id:
        raise TenantMismatch("Warehouse repository returned an out-of-scope object.")


def validate_ingredient(
    ingredient: Ingredient, business_id: int, ingredient_id: int
) -> None:
    if ingredient.business_id != business_id or ingredient.id != ingredient_id:
        raise TenantMismatch("Ingredient repository returned an out-of-scope object.")


def validate_stock(
    stock: Stock,
    business_id: int,
    warehouse_id: int,
    ingredient_id: int,
) -> None:
    key = stock.key
    if (
        key.business_id != business_id
        or key.warehouse_id != warehouse_id
        or key.ingredient_id != ingredient_id
    ):
        raise TenantMismatch("Stock repository returned an out-of-scope projection.")


def validate_movement(movement: StockMovement, business_id: int) -> None:
    if (
        movement.source_identity.business_id != business_id
        or movement.stock_key.business_id != business_id
    ):
        raise TenantMismatch("Movement repository returned an out-of-scope record.")


def result_for(
    stock: Stock,
    movement: StockMovement,
    *,
    idempotent: bool,
) -> StockOperationResult:
    return StockOperationResult(
        stock_key=stock.key,
        current_quantity=stock.quantity,
        current_average_cost=stock.average_cost,
        movement_source_identity=movement.source_identity,
        movement_type=movement.movement_type,
        direction=movement.direction,
        idempotent=idempotent,
    )
