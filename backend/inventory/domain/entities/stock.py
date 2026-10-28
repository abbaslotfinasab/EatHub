from datetime import datetime
from decimal import Decimal, ROUND_HALF_EVEN, localcontext

from inventory.domain.entities.ingredient import Ingredient
from inventory.domain.entities.stock_movement import StockMovement
from inventory.domain.entities.warehouse import Warehouse
from inventory.domain.enums.movement import MovementDirection, MovementType
from inventory.domain.exceptions import (
    InvalidMovement,
    InvalidQuantity,
    InvalidStockKey,
    InvalidUnitCost,
    MovementAlreadyReversed,
    MovementNotReversible,
    NegativeStock,
    TenantMismatch,
)
from inventory.domain.value_objects.decimal_precision import COST_MAX_SCALE
from inventory.domain.value_objects.quantity import Quantity
from inventory.domain.value_objects.reversal_context import ReversalContext
from inventory.domain.value_objects.source_identity import SourceIdentity
from inventory.domain.value_objects.stock_key import StockKey
from inventory.domain.value_objects.unit import Unit
from inventory.domain.value_objects.unit_cost import UnitCost


_CALCULATION_PRECISION = 256
_AVCO_QUANTUM = Decimal(1).scaleb(-COST_MAX_SCALE)


def _precision_for_sum_of_products(*products: tuple[Decimal, Decimal]) -> int:
    product_exponents = [
        left.as_tuple().exponent + right.as_tuple().exponent
        for left, right in products
    ]
    product_adjusted = [
        left.adjusted() + right.adjusted()
        for left, right in products
        if left and right
    ]
    if not product_adjusted:
        return _CALCULATION_PRECISION
    return max(
        _CALCULATION_PRECISION,
        max(product_adjusted) - min(product_exponents) + 2,
        *(
            len(left.as_tuple().digits) + len(right.as_tuple().digits)
            for left, right in products
        ),
    )


def _precision_for_sum(*values: Decimal) -> int:
    lowest_exponent = min(value.as_tuple().exponent for value in values)
    highest_adjusted = max(value.adjusted() for value in values if value)
    return max(
        _CALCULATION_PRECISION,
        highest_adjusted - lowest_exponent + 2,
        *(len(value.as_tuple().digits) for value in values),
    )


class Stock:
    """Current stock state and its invariant-preserving transitions."""

    __slots__ = (
        "_key",
        "_unit",
        "_quantity",
        "_average_cost",
        "_reorder_level",
        "_reorder_quantity",
    )

    def __init__(
        self,
        warehouse: Warehouse,
        ingredient: Ingredient,
        *,
        reorder_level: Quantity | None = None,
        reorder_quantity: Quantity | None = None,
    ) -> None:
        if warehouse.id is None or ingredient.id is None:
            raise InvalidStockKey("Stock requires identified Warehouse and Ingredient.")
        if warehouse.business_id != ingredient.business_id:
            raise TenantMismatch("Warehouse and Ingredient must share a Business.")

        unit = ingredient.canonical_unit
        self._key = StockKey(warehouse.business_id, warehouse.id, ingredient.id)
        self._unit = unit
        self._quantity = Quantity.zero(unit)
        self._average_cost = UnitCost.zero()
        self._reorder_level = self._validated_optional_quantity(reorder_level, unit)
        self._reorder_quantity = self._validated_optional_quantity(
            reorder_quantity, unit
        )

    @classmethod
    def reconstitute(
        cls,
        warehouse: Warehouse,
        ingredient: Ingredient,
        quantity: Quantity,
        average_cost: UnitCost,
        *,
        reorder_level: Quantity | None = None,
        reorder_quantity: Quantity | None = None,
    ) -> "Stock":
        """Restore a persisted projection without loading or replaying movements."""
        if not isinstance(warehouse, Warehouse) or not isinstance(
            ingredient, Ingredient
        ):
            raise InvalidStockKey(
                "Stock reconstitution requires Warehouse and Ingredient."
            )
        if warehouse.id is None or ingredient.id is None:
            raise InvalidStockKey("Stock reconstitution requires identified references.")
        if warehouse.business_id != ingredient.business_id:
            raise TenantMismatch("Warehouse and Ingredient must share a Business.")
        unit = ingredient.canonical_unit
        if not isinstance(quantity, Quantity) or quantity.unit is not unit:
            raise InvalidQuantity("Restored quantity must use the canonical Unit.")
        if not isinstance(average_cost, UnitCost):
            raise InvalidUnitCost("Restored Stock requires an average UnitCost.")
        if quantity.amount == 0 and average_cost.amount != 0:
            raise InvalidUnitCost("Zero Stock must have zero average cost.")

        stock = cls(
            warehouse,
            ingredient,
            reorder_level=reorder_level,
            reorder_quantity=reorder_quantity,
        )
        stock._quantity = quantity
        stock._average_cost = average_cost
        return stock

    @property
    def key(self) -> StockKey:
        return self._key

    @property
    def unit(self) -> Unit:
        return self._unit

    @property
    def quantity(self) -> Quantity:
        return self._quantity

    @property
    def average_cost(self) -> UnitCost:
        return self._average_cost

    @property
    def reorder_level(self) -> Quantity:
        return self._reorder_level

    @property
    def reorder_quantity(self) -> Quantity:
        return self._reorder_quantity

    def receive(
        self,
        quantity: Quantity,
        unit_cost: UnitCost,
        source_identity: SourceIdentity,
        warehouse: Warehouse,
        *,
        actor_id: int | None = None,
        occurred_at: datetime | None = None,
    ) -> StockMovement:
        self._validate_warehouse(warehouse)
        warehouse.ensure_can_receive()
        return self._apply(
            movement_type=MovementType.RECEIPT,
            direction=MovementDirection.IN,
            quantity=quantity,
            unit_cost=unit_cost,
            source_identity=source_identity,
            warehouse=warehouse,
            actor_id=actor_id,
            occurred_at=occurred_at,
        )

    def open_balance(
        self,
        quantity: Quantity,
        unit_cost: UnitCost,
        source_identity: SourceIdentity,
        warehouse: Warehouse,
        *,
        actor_id: int,
        reason: str | None = None,
        occurred_at: datetime | None = None,
    ) -> StockMovement:
        """Initialize a never-used stock position from an audited opening count."""
        self._validate_warehouse(warehouse)
        warehouse.ensure_can_receive()
        if self._quantity.amount != 0 or self._average_cost.amount != 0:
            raise InvalidMovement("Opening balance requires an empty stock position.")
        if isinstance(actor_id, bool) or not isinstance(actor_id, int) or actor_id <= 0:
            raise InvalidMovement("Opening balance requires a positive actor ID.")
        if not isinstance(unit_cost, UnitCost):
            raise InvalidUnitCost("Opening balance requires a unit cost.")
        return self._apply(
            movement_type=MovementType.OPENING_BALANCE,
            direction=MovementDirection.IN,
            quantity=quantity,
            unit_cost=unit_cost,
            source_identity=source_identity,
            warehouse=warehouse,
            reason=reason,
            actor_id=actor_id,
            occurred_at=occurred_at,
        )

    def adjust(
        self,
        quantity: Quantity,
        direction: MovementDirection,
        source_identity: SourceIdentity,
        warehouse: Warehouse,
        *,
        reason: str,
        actor_id: int,
        unit_cost: UnitCost | None = None,
        occurred_at: datetime | None = None,
    ) -> StockMovement:
        if not isinstance(reason, str) or not reason.strip():
            raise InvalidMovement("Adjustment reason is required.")
        if (
            isinstance(actor_id, bool)
            or not isinstance(actor_id, int)
            or actor_id <= 0
        ):
            raise InvalidMovement("Adjustments require a positive actor ID.")
        adjustment_cost = unit_cost or self._average_cost
        if not isinstance(adjustment_cost, UnitCost):
            raise InvalidUnitCost("Adjustment unit cost must be a UnitCost.")
        if direction is MovementDirection.IN:
            self._validate_warehouse(warehouse)
            warehouse.ensure_can_receive()
        elif direction is MovementDirection.OUT:
            adjustment_cost = self._average_cost
        else:
            raise InvalidMovement("Adjustment direction must be IN or OUT.")
        return self._apply(
            movement_type=MovementType.ADJUSTMENT,
            direction=direction,
            quantity=quantity,
            unit_cost=adjustment_cost,
            source_identity=source_identity,
            warehouse=warehouse,
            reason=reason,
            actor_id=actor_id,
            occurred_at=occurred_at,
        )

    def issue(
        self,
        quantity: Quantity,
        source_identity: SourceIdentity,
        warehouse: Warehouse,
        *,
        reason: str,
        actor_id: int,
        occurred_at: datetime | None = None,
    ) -> StockMovement:
        if not isinstance(reason, str) or not reason.strip():
            raise InvalidMovement("Issue reason is required.")
        if isinstance(actor_id, bool) or not isinstance(actor_id, int) or actor_id <= 0:
            raise InvalidMovement("Issues require a positive actor ID.")
        self._validate_warehouse(warehouse)
        warehouse.ensure_active()
        return self._apply(
            movement_type=MovementType.ISSUE,
            direction=MovementDirection.OUT,
            quantity=quantity,
            unit_cost=self._average_cost,
            source_identity=source_identity,
            warehouse=warehouse,
            reason=reason,
            actor_id=actor_id,
            occurred_at=occurred_at,
        )

    def transfer_out(
        self,
        quantity: Quantity,
        source_identity: SourceIdentity,
        warehouse: Warehouse,
        *,
        actor_id: int,
        occurred_at: datetime | None = None,
    ) -> StockMovement:
        self._validate_warehouse(warehouse)
        warehouse.ensure_active()
        if isinstance(actor_id, bool) or not isinstance(actor_id, int) or actor_id <= 0:
            raise InvalidMovement("Transfers require a positive actor ID.")
        return self._apply(
            movement_type=MovementType.TRANSFER_DISPATCH,
            direction=MovementDirection.OUT,
            quantity=quantity,
            unit_cost=self._average_cost,
            source_identity=source_identity,
            warehouse=warehouse,
            actor_id=actor_id,
            occurred_at=occurred_at,
        )

    def transfer_in(
        self,
        quantity: Quantity,
        unit_cost: UnitCost,
        source_identity: SourceIdentity,
        warehouse: Warehouse,
        *,
        actor_id: int,
        occurred_at: datetime | None = None,
    ) -> StockMovement:
        self._validate_warehouse(warehouse)
        warehouse.ensure_can_receive()
        return self._apply(
            movement_type=MovementType.TRANSFER_RECEIPT,
            direction=MovementDirection.IN,
            quantity=quantity,
            unit_cost=unit_cost,
            source_identity=source_identity,
            warehouse=warehouse,
            actor_id=actor_id,
            occurred_at=occurred_at,
        )

    def reverse(
        self,
        original: StockMovement,
        source_identity: SourceIdentity,
        warehouse: Warehouse,
        *,
        context: ReversalContext,
        reason: str | None = None,
        actor_id: int | None = None,
        occurred_at: datetime | None = None,
    ) -> StockMovement:
        """Undo the latest effective movement using trusted Application context.

        Application supplies whether the movement was already reversed and the
        latest effective movement identity; Domain does not query a ledger.
        """
        if not isinstance(original, StockMovement):
            raise InvalidMovement("Reversal requires an existing StockMovement.")
        if not isinstance(context, ReversalContext):
            raise InvalidMovement("Reversal requires application movement context.")
        if context.already_reversed:
            raise MovementAlreadyReversed("This movement has already been reversed.")
        if context.latest_effective_source_identity != original.source_identity:
            raise MovementNotReversible(
                "Only the latest effective Stock movement may be reversed."
            )
        if original.stock_key != self._key:
            raise TenantMismatch("Cannot reverse a movement from another Stock.")
        if (
            original.balance_after.unit is not self._unit
            or original.balance_after.amount != self._quantity.amount
        ):
            raise MovementNotReversible(
                "Current Stock does not match the movement's resulting balance."
            )
        direction = (
            MovementDirection.OUT
            if original.direction is MovementDirection.IN
            else MovementDirection.IN
        )
        reversal_unit_cost = original.unit_cost
        if original.direction is MovementDirection.IN:
            reversed_quantity = original.quantity.convert_to(self._unit)
            if reversed_quantity.amount > self._quantity.amount:
                raise NegativeStock("Reversal cannot make Stock negative.")
            resulting_quantity = self._quantity - reversed_quantity
        else:
            resulting_quantity = self._quantity + original.quantity.convert_to(self._unit)
        if resulting_quantity.amount == 0 and original.average_cost_before.amount != 0:
            raise InvalidMovement(
                "Reversal context conflicts with the movement's prior average cost."
            )
        if direction is MovementDirection.IN:
            self._validate_warehouse(warehouse)
            warehouse.ensure_can_receive()
        movement = self._apply(
            movement_type=MovementType.REVERSAL,
            direction=direction,
            quantity=original.quantity,
            unit_cost=reversal_unit_cost,
            source_identity=source_identity,
            warehouse=warehouse,
            reason=reason,
            actor_id=actor_id,
            reverses=original.source_identity,
            occurred_at=occurred_at,
            resulting_average_cost=original.average_cost_before,
        )
        return movement

    def _apply(
        self,
        *,
        movement_type: MovementType,
        direction: MovementDirection,
        quantity: Quantity,
        unit_cost: UnitCost,
        source_identity: SourceIdentity,
        warehouse: Warehouse,
        reason: str | None = None,
        actor_id: int | None = None,
        reverses: SourceIdentity | None = None,
        occurred_at: datetime | None = None,
        resulting_average_cost: UnitCost | None = None,
    ) -> StockMovement:
        self._validate_warehouse(warehouse)
        self._validate_source(source_identity)
        if not isinstance(quantity, Quantity) or quantity.amount <= 0:
            raise InvalidQuantity("Movement quantity must be strictly positive.")
        if not isinstance(unit_cost, UnitCost):
            raise InvalidUnitCost("Stock transitions require a UnitCost.")
        if not isinstance(direction, MovementDirection):
            raise InvalidMovement("Movement direction must be IN or OUT.")
        normalized = quantity.convert_to(self._unit)

        if direction is MovementDirection.IN:
            new_quantity = self._quantity + normalized
            new_average_cost = resulting_average_cost or self._weighted_average(
                unit_cost, normalized
            )
        else:
            if normalized.amount > self._quantity.amount:
                raise NegativeStock("Stock cannot become negative.")
            new_quantity = self._quantity - normalized
            new_average_cost = (
                UnitCost.zero()
                if new_quantity.amount == 0
                else resulting_average_cost or self._average_cost
            )

        movement = StockMovement._record(
            stock_key=self._key,
            movement_type=movement_type,
            direction=direction,
            quantity=normalized,
            unit_cost=unit_cost,
            source_identity=source_identity,
            balance_after=new_quantity,
            average_cost_before=self._average_cost,
            reason=reason.strip() if isinstance(reason, str) else reason,
            actor_id=actor_id,
            reverses=reverses,
            occurred_at=occurred_at,
        )
        self._quantity = new_quantity
        self._average_cost = new_average_cost
        return movement

    def _weighted_average(
        self,
        received_unit_cost: UnitCost,
        received_quantity: Quantity,
    ) -> UnitCost:
        if self._quantity.amount == 0:
            return received_unit_cost
        old_quantity = self._quantity.amount
        old_average = self._average_cost.amount
        new_quantity = received_quantity.amount
        received_cost = received_unit_cost.amount
        # V1 valuation is a Domain rule: calculate with ample guard precision,
        # then round the resulting projection once to the UnitCost scale.
        # This keeps every valid AVCO projection exactly storable and reversible.
        with localcontext() as context:
            context.prec = max(
                _CALCULATION_PRECISION,
                _precision_for_sum_of_products(
                    (old_quantity, old_average), (new_quantity, received_cost)
                ),
                _precision_for_sum(old_quantity, new_quantity),
            )
            context.rounding = ROUND_HALF_EVEN
            resulting_quantity = old_quantity + new_quantity
            total_value = (
                old_quantity * old_average + new_quantity * received_cost
            )
            average = (total_value / resulting_quantity).quantize(
                _AVCO_QUANTUM,
                rounding=ROUND_HALF_EVEN,
            )
            return UnitCost(average)

    def _validate_warehouse(self, warehouse: Warehouse) -> None:
        if (
            warehouse.business_id != self._key.business_id
            or warehouse.id != self._key.warehouse_id
        ):
            raise TenantMismatch("Warehouse does not belong to this Stock position.")

    def _validate_source(self, source_identity: SourceIdentity) -> None:
        if (
            not isinstance(source_identity, SourceIdentity)
            or source_identity.business_id != self._key.business_id
        ):
            raise TenantMismatch("Operation source belongs to another Business.")

    @staticmethod
    def _validated_optional_quantity(
        quantity: Quantity | None,
        unit: Unit,
    ) -> Quantity:
        if quantity is None:
            return Quantity.zero(unit)
        if quantity.unit is not unit:
            raise InvalidQuantity("Reorder values must use the Ingredient unit.")
        return quantity
