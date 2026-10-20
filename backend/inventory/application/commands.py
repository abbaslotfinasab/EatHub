from dataclasses import dataclass
from decimal import Decimal

from inventory.application.exceptions import InvalidApplicationInput
from inventory.domain.enums.movement import MovementDirection
from inventory.domain.value_objects.quantity import Quantity
from inventory.domain.value_objects.source_identity import SourceIdentity


@dataclass(frozen=True, slots=True)
class OperationIdentityInput:
    """Source identity fields excluding Business, which comes from trusted context."""

    source_type: str
    source_document_id: int
    source_line_id: int
    operation_kind: str

    def __post_init__(self) -> None:
        if not isinstance(self.source_type, str) or not self.source_type.strip():
            raise InvalidApplicationInput("Source type is required.")
        if not isinstance(self.operation_kind, str) or not self.operation_kind.strip():
            raise InvalidApplicationInput("Operation kind is required.")
        for value, label in (
            (self.source_document_id, "Source document ID"),
            (self.source_line_id, "Source line ID"),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise InvalidApplicationInput(f"{label} must be a positive integer.")
        object.__setattr__(self, "source_type", self.source_type.strip())
        object.__setattr__(self, "operation_kind", self.operation_kind.strip())

    def to_domain(self, business_id: int) -> SourceIdentity:
        return SourceIdentity(
            business_id=business_id,
            source_type=self.source_type,
            source_document_id=self.source_document_id,
            source_line_id=self.source_line_id,
            operation_kind=self.operation_kind,
        )


def _validate_resource_ids(warehouse_id: int, ingredient_id: int) -> None:
    for value, label in (
        (warehouse_id, "Warehouse ID"),
        (ingredient_id, "Ingredient ID"),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise InvalidApplicationInput(f"{label} must be a positive integer.")


def _validate_ingredient_id(ingredient_id: int) -> None:
    if isinstance(ingredient_id, bool) or not isinstance(ingredient_id, int) or ingredient_id <= 0:
        raise InvalidApplicationInput("Ingredient ID must be a positive integer.")


@dataclass(frozen=True, slots=True)
class ReceiveStockCommand:
    warehouse_id: int | None
    ingredient_id: int
    quantity_amount: Decimal | int | str
    quantity_unit: str
    unit_cost_amount: Decimal | int | str
    unit_cost_unit: str
    source: OperationIdentityInput

    def __post_init__(self) -> None:
        _validate_ingredient_id(self.ingredient_id)
        if self.warehouse_id is not None:
            if isinstance(self.warehouse_id, bool) or not isinstance(self.warehouse_id, int) or self.warehouse_id <= 0:
                raise InvalidApplicationInput("Warehouse ID must be a positive integer or None.")
        for value, label in (
            (self.quantity_amount, "Quantity"),
            (self.unit_cost_amount, "Unit cost"),
        ):
            if isinstance(value, (float, bool)) or not isinstance(
                value, (Decimal, int, str)
            ):
                raise InvalidApplicationInput(f"{label} must be exact Decimal data.")
        if not isinstance(self.quantity_unit, str) or not self.quantity_unit.strip():
            raise InvalidApplicationInput("Receive quantity unit is required.")
        if not isinstance(self.unit_cost_unit, str) or not self.unit_cost_unit.strip():
            raise InvalidApplicationInput("Unit cost basis unit is required.")
        if not isinstance(self.source, OperationIdentityInput):
            raise InvalidApplicationInput("Receive command requires source identity data.")


@dataclass(frozen=True, slots=True)
class AdjustStockCommand:
    warehouse_id: int
    ingredient_id: int
    quantity: Quantity
    direction: MovementDirection
    reason: str
    source: OperationIdentityInput

    def __post_init__(self) -> None:
        _validate_resource_ids(self.warehouse_id, self.ingredient_id)
        if not isinstance(self.quantity, Quantity):
            raise InvalidApplicationInput("Adjustment command requires a Quantity.")
        if not isinstance(self.direction, MovementDirection):
            raise InvalidApplicationInput("Adjustment direction is invalid.")
        if not isinstance(self.reason, str):
            raise InvalidApplicationInput("Adjustment reason must be text.")
        if not isinstance(self.source, OperationIdentityInput):
            raise InvalidApplicationInput("Adjustment command requires source identity data.")


@dataclass(frozen=True, slots=True)
class ReverseStockMovementCommand:
    target: OperationIdentityInput
    source: OperationIdentityInput
    reason: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.target, OperationIdentityInput):
            raise InvalidApplicationInput("Reversal command requires a target identity.")
        if not isinstance(self.source, OperationIdentityInput):
            raise InvalidApplicationInput("Reversal command requires a new source identity.")
        if self.reason is not None and not isinstance(self.reason, str):
            raise InvalidApplicationInput("Reversal reason must be text or None.")
