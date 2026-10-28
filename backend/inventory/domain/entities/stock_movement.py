from dataclasses import dataclass
from datetime import datetime

from inventory.domain.enums.movement import MovementDirection, MovementType
from inventory.domain.exceptions import InvalidMovement
from inventory.domain.value_objects.quantity import Quantity
from inventory.domain.value_objects.source_identity import SourceIdentity
from inventory.domain.value_objects.stock_key import StockKey
from inventory.domain.value_objects.unit_cost import UnitCost


@dataclass(frozen=True, slots=True, init=False)
class StockMovement:
    """Immutable historical movement recorded by Stock or reconstituted as history.

    ``balance_after`` is a historical snapshot, never the current balance.
    ``average_cost_before`` preserves the exact prior projection so a permitted
    latest-only reversal does not need to reconstruct rounded AVCO history.
    """

    stock_key: StockKey
    movement_type: MovementType
    direction: MovementDirection
    quantity: Quantity
    unit_cost: UnitCost
    source_identity: SourceIdentity
    balance_after: Quantity
    average_cost_before: UnitCost
    reason: str | None
    actor_id: int | None
    reverses: SourceIdentity | None
    occurred_at: datetime | None

    def __init__(self) -> None:
        raise TypeError("Use a Stock transition or reconstitute() to create movement state.")

    @classmethod
    def _record(
        cls,
        *,
        stock_key: StockKey,
        movement_type: MovementType,
        direction: MovementDirection,
        quantity: Quantity,
        unit_cost: UnitCost,
        source_identity: SourceIdentity,
        balance_after: Quantity,
        average_cost_before: UnitCost,
        reason: str | None = None,
        actor_id: int | None = None,
        reverses: SourceIdentity | None = None,
        occurred_at: datetime | None = None,
    ) -> "StockMovement":
        cls._validate(
            stock_key=stock_key,
            movement_type=movement_type,
            direction=direction,
            quantity=quantity,
            unit_cost=unit_cost,
            source_identity=source_identity,
            balance_after=balance_after,
            average_cost_before=average_cost_before,
            reason=reason,
            actor_id=actor_id,
            reverses=reverses,
            occurred_at=occurred_at,
        )
        movement = object.__new__(cls)
        for name, value in locals().copy().items():
            if name in cls.__dataclass_fields__:
                object.__setattr__(movement, name, value)
        return movement

    @classmethod
    def reconstitute(
        cls,
        *,
        stock_key: StockKey,
        movement_type: MovementType,
        direction: MovementDirection,
        quantity: Quantity,
        unit_cost: UnitCost,
        source_identity: SourceIdentity,
        balance_after: Quantity,
        average_cost_before: UnitCost,
        reason: str | None = None,
        actor_id: int | None = None,
        reverses: SourceIdentity | None = None,
        occurred_at: datetime | None = None,
    ) -> "StockMovement":
        """Rebuild existing immutable movement state without applying a transition.

        All fields pass through the same Domain validation as a newly recorded
        movement. This factory does not calculate valuation or mutate Stock.
        """
        return cls._record(
            stock_key=stock_key,
            movement_type=movement_type,
            direction=direction,
            quantity=quantity,
            unit_cost=unit_cost,
            source_identity=source_identity,
            balance_after=balance_after,
            average_cost_before=average_cost_before,
            reason=reason,
            actor_id=actor_id,
            reverses=reverses,
            occurred_at=occurred_at,
        )

    @staticmethod
    def _validate(
        *,
        stock_key: StockKey,
        movement_type: MovementType,
        direction: MovementDirection,
        quantity: Quantity,
        unit_cost: UnitCost,
        source_identity: SourceIdentity,
        balance_after: Quantity,
        average_cost_before: UnitCost,
        reason: str | None,
        actor_id: int | None,
        reverses: SourceIdentity | None,
        occurred_at: datetime | None,
    ) -> None:
        if not isinstance(movement_type, MovementType):
            raise InvalidMovement("Movement type is invalid.")
        if not isinstance(direction, MovementDirection):
            raise InvalidMovement("Movement direction must be IN or OUT.")
        StockMovement.validate_semantics(movement_type, direction)
        if not isinstance(quantity, Quantity) or quantity.amount <= 0:
            raise InvalidMovement("Movement quantity must be strictly positive.")
        if not isinstance(unit_cost, UnitCost):
            raise InvalidMovement("Movement requires a UnitCost value.")
        if not isinstance(average_cost_before, UnitCost):
            raise InvalidMovement("Movement requires the prior average cost snapshot.")
        if not isinstance(stock_key, StockKey):
            raise InvalidMovement("Movement requires a StockKey.")
        if not isinstance(source_identity, SourceIdentity):
            raise InvalidMovement("Movement requires a source identity.")
        if source_identity.business_id != stock_key.business_id:
            raise InvalidMovement("Movement source belongs to another Business.")
        if balance_after.unit is not quantity.unit:
            raise InvalidMovement("Balance snapshot must use the movement unit.")
        if balance_after.amount < 0:
            raise InvalidMovement("Balance snapshot cannot be negative.")
        if movement_type is MovementType.ADJUSTMENT:
            if not isinstance(reason, str) or not reason.strip():
                raise InvalidMovement("Adjustment reason is required.")
            if (
                isinstance(actor_id, bool)
                or not isinstance(actor_id, int)
                or actor_id <= 0
            ):
                raise InvalidMovement("Adjustment movement requires an actor ID.")
        if movement_type is MovementType.ISSUE and (
            not isinstance(reason, str) or not reason.strip()
        ):
            raise InvalidMovement("Issue movement requires a reason.")
        if movement_type in (
            MovementType.ISSUE,
            MovementType.TRANSFER_DISPATCH,
            MovementType.TRANSFER_RECEIPT,
            MovementType.OPENING_BALANCE,
        ) and (
            isinstance(actor_id, bool) or not isinstance(actor_id, int) or actor_id <= 0
        ):
            raise InvalidMovement("This movement requires a positive actor ID.")
        if movement_type is MovementType.REVERSAL:
            if not isinstance(reverses, SourceIdentity):
                raise InvalidMovement("Reversal must identify the operation reversed.")
            if reverses.business_id != stock_key.business_id:
                raise InvalidMovement("Reversed operation belongs to another Business.")
        elif reverses is not None:
            raise InvalidMovement("Only reversal movements may reference a reversal.")
        if actor_id is not None and (
            isinstance(actor_id, bool) or not isinstance(actor_id, int) or actor_id <= 0
        ):
            raise InvalidMovement("Actor ID must be a positive integer or None.")
        if occurred_at is not None and not isinstance(occurred_at, datetime):
            raise InvalidMovement("Movement timestamp must be a datetime or None.")

    @staticmethod
    def validate_semantics(
        movement_type: MovementType,
        direction: MovementDirection,
    ) -> None:
        if not isinstance(movement_type, MovementType):
            raise InvalidMovement("Movement type is invalid.")
        if not isinstance(direction, MovementDirection):
            raise InvalidMovement("Movement direction must be IN or OUT.")
        if (
            movement_type is MovementType.RECEIPT
            and direction is not MovementDirection.IN
        ):
            raise InvalidMovement("Receipt movements must have IN direction.")
        if (
            movement_type in (MovementType.ISSUE, MovementType.TRANSFER_DISPATCH)
            and direction is not MovementDirection.OUT
        ):
            raise InvalidMovement("Issue and transfer dispatch movements must be OUT.")
        if (
            movement_type is MovementType.TRANSFER_RECEIPT
            and direction is not MovementDirection.IN
        ):
            raise InvalidMovement("Transfer receipt movements must be IN.")
        if (
            movement_type is MovementType.OPENING_BALANCE
            and direction is not MovementDirection.IN
        ):
            raise InvalidMovement("Opening balance movements must be IN.")
