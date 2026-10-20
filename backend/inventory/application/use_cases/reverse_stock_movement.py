from inventory.application.commands import ReverseStockMovementCommand
from inventory.application.context import InventoryExecutionContext
from inventory.application.dto.stock_operation import StockOperationResult
from inventory.application.exceptions import (
    OperationConflict,
    ResourceNotFound,
    StockProjectionConflict,
)
from inventory.application.ports.repositories import (
    IngredientRepository,
    StockMovementRepository,
    StockRepository,
    WarehouseRepository,
)
from inventory.application.ports.unit_of_work import InventoryUnitOfWork
from inventory.application.use_cases._common import (
    require_context,
    result_for,
    validate_ingredient,
    validate_movement,
    validate_stock,
    validate_warehouse,
)
from inventory.domain.entities.stock_movement import StockMovement
from inventory.domain.enums.movement import MovementDirection, MovementType
from inventory.domain.exceptions import TenantMismatch
from inventory.domain.value_objects.reversal_context import ReversalContext
from inventory.domain.value_objects.source_identity import SourceIdentity


class ReverseStockMovementUseCase:
    def __init__(
        self,
        warehouses: WarehouseRepository,
        ingredients: IngredientRepository,
        stocks: StockRepository,
        movements: StockMovementRepository,
        unit_of_work: InventoryUnitOfWork,
    ) -> None:
        self._warehouses = warehouses
        self._ingredients = ingredients
        self._stocks = stocks
        self._movements = movements
        self._unit_of_work = unit_of_work

    def execute(
        self,
        command: ReverseStockMovementCommand,
        context: InventoryExecutionContext,
    ) -> StockOperationResult:
        context = require_context(context)
        if not isinstance(command, ReverseStockMovementCommand):
            raise TypeError("ReverseStockMovementUseCase requires its command type.")
        target_identity = command.target.to_domain(context.business_id)
        reversal_identity = command.source.to_domain(context.business_id)

        with self._unit_of_work.atomic():
            original = self._movements.find_by_source_identity_for_business(
                context.business_id, target_identity
            )
            if original is None:
                raise ResourceNotFound("Target movement was not found in this Business.")
            validate_movement(original, context.business_id)

            existing_reversal = self._movements.find_by_source_identity_for_business(
                context.business_id, reversal_identity
            )
            if existing_reversal is not None:
                validate_movement(existing_reversal, context.business_id)
                if not self._matches_reversal(
                    existing_reversal,
                    original,
                    reversal_identity,
                    command.reason,
                    context.actor_id,
                ):
                    raise OperationConflict(
                        "Source identity already exists with different reversal data."
                    )
                stock = self._stocks.get_for_business(
                    context.business_id,
                    original.stock_key.warehouse_id,
                    original.stock_key.ingredient_id,
                )
                if stock is None:
                    raise ResourceNotFound("Stock projection for reversal is missing.")
                validate_stock(
                    stock,
                    context.business_id,
                    original.stock_key.warehouse_id,
                    original.stock_key.ingredient_id,
                )
                return result_for(stock, existing_reversal, idempotent=True)

            warehouse = self._warehouses.get_by_id_for_business(
                original.stock_key.warehouse_id, context.business_id
            )
            if warehouse is None:
                raise ResourceNotFound("Movement Warehouse was not found in this Business.")
            validate_warehouse(
                warehouse, context.business_id, original.stock_key.warehouse_id
            )
            ingredient = self._ingredients.get_by_id_for_business(
                original.stock_key.ingredient_id, context.business_id
            )
            if ingredient is None:
                raise ResourceNotFound("Movement Ingredient was not found in this Business.")
            validate_ingredient(
                ingredient, context.business_id, original.stock_key.ingredient_id
            )
            if warehouse.business_id != ingredient.business_id:
                raise TenantMismatch("Movement Warehouse and Ingredient cross Business scope.")

            stock = self._stocks.get_for_business(
                context.business_id,
                original.stock_key.warehouse_id,
                original.stock_key.ingredient_id,
            )
            if stock is None:
                raise ResourceNotFound("Stock projection was not found in this Business.")
            validate_stock(
                stock,
                context.business_id,
                original.stock_key.warehouse_id,
                original.stock_key.ingredient_id,
            )
            already_reversed = self._movements.has_reversal_for_source(
                context.business_id, original.source_identity
            )
            latest = self._movements.get_latest_effective_for_stock(
                context.business_id, original.stock_key
            )
            reversal_context = ReversalContext(
                latest_effective_source_identity=(
                    latest.source_identity if latest is not None else None
                ),
                already_reversed=already_reversed,
            )
            if (
                not already_reversed
                and latest is not None
                and latest.source_identity == original.source_identity
                and stock.quantity != original.balance_after
            ):
                raise StockProjectionConflict(
                    "Current Stock quantity does not match the target movement balance."
                )
            movement = stock.reverse(
                original,
                reversal_identity,
                warehouse,
                context=reversal_context,
                reason=command.reason,
                actor_id=context.actor_id,
            )
            self._stocks.save(stock)
            self._movements.save(movement)
            return result_for(stock, movement, idempotent=False)

    @staticmethod
    def _matches_reversal(
        movement: StockMovement,
        original: StockMovement,
        reversal_identity: SourceIdentity,
        reason: str | None,
        actor_id: int | None,
    ) -> bool:
        expected_direction = (
            MovementDirection.OUT
            if original.direction is MovementDirection.IN
            else MovementDirection.IN
        )
        expected_reason = reason.strip() if isinstance(reason, str) else reason
        return (
            movement.source_identity == reversal_identity
            and movement.stock_key == original.stock_key
            and movement.movement_type is MovementType.REVERSAL
            and movement.direction is expected_direction
            and movement.quantity == original.quantity
            and movement.reverses == original.source_identity
            and movement.reason == expected_reason
            and movement.actor_id == actor_id
        )
