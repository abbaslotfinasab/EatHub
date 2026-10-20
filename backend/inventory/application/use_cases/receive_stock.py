from decimal import Decimal, localcontext

from inventory.application.commands import ReceiveStockCommand
from inventory.application.context import InventoryExecutionContext
from inventory.application.dto.stock_operation import StockOperationResult
from inventory.application.exceptions import (
    InvalidApplicationInput,
    OperationConflict,
    ResourceNotFound,
    WarehouseConfigurationError,
)
from inventory.application.ports.repositories import (
    IngredientRepository,
    StockMovementRepository,
    StockRepository,
    WarehouseRepository,
)
from inventory.application.ports.unit_of_work import InventoryUnitOfWork
from inventory.application.use_cases._common import (
    result_for,
    require_context,
    validate_ingredient,
    validate_movement,
    validate_stock,
    validate_warehouse,
)
from inventory.domain.entities.stock_movement import StockMovement
from inventory.domain.enums.movement import MovementDirection, MovementType
from inventory.domain.exceptions import TenantMismatch
from inventory.domain.value_objects.decimal_precision import (
    COST_MAX_INTEGER_DIGITS,
    COST_MAX_SCALE,
)
from inventory.domain.value_objects.quantity import Quantity
from inventory.domain.value_objects.source_identity import SourceIdentity
from inventory.domain.value_objects.unit import Unit
from inventory.domain.value_objects.unit_cost import UnitCost


class ReceiveStockUseCase:
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
        command: ReceiveStockCommand,
        context: InventoryExecutionContext,
    ) -> StockOperationResult:
        context = require_context(context)
        if not isinstance(command, ReceiveStockCommand):
            raise TypeError("ReceiveStockUseCase requires ReceiveStockCommand.")

        with self._unit_of_work.atomic():
            ingredient = self._ingredients.get_by_id_for_business(
                command.ingredient_id, context.business_id
            )
            if ingredient is None:
                raise ResourceNotFound("Ingredient was not found in this Business.")
            validate_ingredient(ingredient, context.business_id, command.ingredient_id)

            warehouse_id = command.warehouse_id
            if warehouse_id is None:
                defaults = self._warehouses.get_active_defaults_for_business(
                    context.business_id
                )
                if len(defaults) != 1:
                    raise WarehouseConfigurationError(
                        "Receipt requires exactly one active default Warehouse; "
                        f"found {len(defaults)}. Configure a single active default."
                    )
                warehouse = defaults[0]
                warehouse_id = warehouse.id
            else:
                warehouse = self._warehouses.get_by_id_for_business(
                    warehouse_id, context.business_id
                )
            if warehouse is None:
                raise ResourceNotFound("Warehouse was not found in this Business.")
            validate_warehouse(warehouse, context.business_id, warehouse_id)
            warehouse.ensure_can_receive()
            if warehouse.business_id != ingredient.business_id:
                raise TenantMismatch("Warehouse and Ingredient must share a Business.")

            try:
                quantity_unit = Unit(command.quantity_unit)
                cost_unit = Unit(command.unit_cost_unit)
                quantity = Quantity(
                    command.quantity_amount, quantity_unit
                ).convert_to(ingredient.canonical_unit)
                purchase_unit_cost = _as_decimal(command.unit_cost_amount)
                if purchase_unit_cost < 0:
                    raise InvalidApplicationInput("Unit cost cannot be negative.")
                canonical_unit_amount = Quantity(
                    Decimal("1"), cost_unit
                ).convert_to(ingredient.canonical_unit).amount
                # Supported conversions have exact power-of-ten ratios. Cost
                # normalization is therefore exact; no intermediate rounding.
                with localcontext() as decimal_context:
                    decimal_context.prec = max(
                        COST_MAX_INTEGER_DIGITS + COST_MAX_SCALE,
                        len(purchase_unit_cost.as_tuple().digits)
                        + abs(purchase_unit_cost.as_tuple().exponent)
                        + 8,
                    )
                    unit_cost = UnitCost(
                        purchase_unit_cost / canonical_unit_amount
                    )
            except ValueError as error:
                raise InvalidApplicationInput(str(error)) from error

            identity = command.source.to_domain(context.business_id)
            existing = self._movements.find_by_source_identity_for_business(
                context.business_id, identity
            )
            if existing is not None:
                validate_movement(existing, context.business_id)
                if not self._matches_receive(
                    existing, command, quantity, unit_cost, identity,
                    context.business_id, warehouse_id
                ):
                    raise OperationConflict(
                        "Source identity already exists with different receipt data."
                    )
                stock = self._stocks.get_for_business(
                    context.business_id, warehouse_id, command.ingredient_id
                )
                if stock is None:
                    raise ResourceNotFound(
                        "Stock projection for existing receipt is missing."
                    )
                validate_stock(stock, context.business_id, warehouse_id, command.ingredient_id)
                return result_for(stock, existing, idempotent=True)

            stock = self._stocks.get_or_create_for_business(
                context.business_id, warehouse, ingredient
            )
            validate_stock(stock, context.business_id, warehouse_id, command.ingredient_id)
            # Re-check after the stock projection lock to resolve concurrent
            # duplicate operations before applying another transition.
            existing = self._movements.find_by_source_identity_for_business(
                context.business_id, identity
            )
            if existing is not None:
                validate_movement(existing, context.business_id)
                if not self._matches_receive(
                    existing, command, quantity, unit_cost, identity,
                    context.business_id, warehouse_id
                ):
                    raise OperationConflict(
                        "Source identity already exists with different receipt data."
                    )
                return result_for(stock, existing, idempotent=True)

            movement = stock.receive(
                quantity,
                unit_cost,
                identity,
                warehouse,
                actor_id=context.actor_id,
            )
            self._stocks.save(stock)
            self._movements.save(movement)
            return result_for(stock, movement, idempotent=False)

    @staticmethod
    def _matches_receive(
        movement: StockMovement,
        command: ReceiveStockCommand,
        quantity: Quantity,
        unit_cost: UnitCost,
        identity: SourceIdentity,
        business_id: int,
        warehouse_id: int,
    ) -> bool:
        return (
            movement.source_identity == identity
            and movement.stock_key.business_id == business_id
            and movement.stock_key.warehouse_id == warehouse_id
            and movement.stock_key.ingredient_id == command.ingredient_id
            and movement.movement_type is MovementType.RECEIPT
            and movement.direction is MovementDirection.IN
            and movement.quantity == quantity
            and movement.unit_cost == unit_cost
        )


def _as_decimal(value: Decimal | int | str) -> Decimal:
    if isinstance(value, (bool, float)):
        raise InvalidApplicationInput("Unit cost must not use float or bool.")
    try:
        result = value if isinstance(value, Decimal) else Decimal(value)
    except (TypeError, ValueError, ArithmeticError) as error:
        raise InvalidApplicationInput("Unit cost must be Decimal-compatible.") from error
    if not result.is_finite():
        raise InvalidApplicationInput("Unit cost must be finite.")
    return result
