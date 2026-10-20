from inventory.application.commands import AdjustStockCommand
from inventory.application.context import InventoryExecutionContext
from inventory.application.dto.stock_operation import StockOperationResult
from inventory.application.exceptions import OperationConflict, ResourceNotFound
from inventory.application.ports.repositories import (
    IngredientRepository,
    StockMovementRepository,
    StockRepository,
    WarehouseRepository,
)
from inventory.application.ports.unit_of_work import InventoryUnitOfWork
from inventory.application.use_cases._common import (
    require_actor,
    require_context,
    result_for,
    validate_ingredient,
    validate_movement,
    validate_stock,
    validate_warehouse,
)
from inventory.domain.entities.stock_movement import StockMovement
from inventory.domain.enums.movement import MovementType
from inventory.domain.exceptions import TenantMismatch
from inventory.domain.value_objects.quantity import Quantity
from inventory.domain.value_objects.source_identity import SourceIdentity


class AdjustStockUseCase:
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
        command: AdjustStockCommand,
        context: InventoryExecutionContext,
    ) -> StockOperationResult:
        context = require_context(context)
        if not isinstance(command, AdjustStockCommand):
            raise TypeError("AdjustStockUseCase requires AdjustStockCommand.")
        actor_id = require_actor(context)

        with self._unit_of_work.atomic():
            warehouse = self._warehouses.get_by_id_for_business(
                command.warehouse_id, context.business_id
            )
            if warehouse is None:
                raise ResourceNotFound("Warehouse was not found in this Business.")
            validate_warehouse(warehouse, context.business_id, command.warehouse_id)
            ingredient = self._ingredients.get_by_id_for_business(
                command.ingredient_id, context.business_id
            )
            if ingredient is None:
                raise ResourceNotFound("Ingredient was not found in this Business.")
            validate_ingredient(ingredient, context.business_id, command.ingredient_id)
            if warehouse.business_id != ingredient.business_id:
                raise TenantMismatch("Warehouse and Ingredient must share a Business.")

            quantity = command.quantity.convert_to(ingredient.canonical_unit)
            identity = command.source.to_domain(context.business_id)
            existing = self._movements.find_by_source_identity_for_business(
                context.business_id, identity
            )
            if existing is not None:
                validate_movement(existing, context.business_id)
                if not self._matches_adjustment(
                    existing, command, quantity, identity, context.business_id, actor_id
                ):
                    raise OperationConflict(
                        "Source identity already exists with different adjustment data."
                    )
                stock = self._stocks.get_for_business(
                    context.business_id,
                    command.warehouse_id,
                    command.ingredient_id,
                )
                if stock is None:
                    raise ResourceNotFound("Stock projection for existing adjustment is missing.")
                validate_stock(
                    stock,
                    context.business_id,
                    command.warehouse_id,
                    command.ingredient_id,
                )
                return result_for(stock, existing, idempotent=True)

            stock = self._stocks.get_for_business(
                context.business_id,
                command.warehouse_id,
                command.ingredient_id,
            )
            if stock is None:
                raise ResourceNotFound("Stock position was not found in this Business.")
            validate_stock(
                stock,
                context.business_id,
                command.warehouse_id,
                command.ingredient_id,
            )
            # Re-check after the repository has obtained the current mutable
            # Stock projection. This closes the check-then-act window for two
            # same-key adjustment requests without exposing locking to
            # Application or depending on a database implementation.
            existing = self._movements.find_by_source_identity_for_business(
                context.business_id, identity
            )
            if existing is not None:
                validate_movement(existing, context.business_id)
                if not self._matches_adjustment(
                    existing, command, quantity, identity, context.business_id, actor_id
                ):
                    raise OperationConflict(
                        "Source identity already exists with different adjustment data."
                    )
                return result_for(stock, existing, idempotent=True)

            movement = stock.adjust(
                command.quantity,
                command.direction,
                identity,
                warehouse,
                reason=command.reason,
                actor_id=actor_id,
            )
            self._stocks.save(stock)
            self._movements.save(movement)
            return result_for(stock, movement, idempotent=False)

    @staticmethod
    def _matches_adjustment(
        movement: StockMovement,
        command: AdjustStockCommand,
        quantity: Quantity,
        identity: SourceIdentity,
        business_id: int,
        actor_id: int,
    ) -> bool:
        return (
            movement.source_identity == identity
            and movement.stock_key.business_id == business_id
            and movement.stock_key.warehouse_id == command.warehouse_id
            and movement.stock_key.ingredient_id == command.ingredient_id
            and movement.movement_type is MovementType.ADJUSTMENT
            and movement.direction is command.direction
            and movement.quantity == quantity
            and movement.reason == command.reason.strip()
            and movement.actor_id == actor_id
        )
