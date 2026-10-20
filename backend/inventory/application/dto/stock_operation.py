from dataclasses import dataclass

from inventory.domain.enums.movement import MovementDirection, MovementType
from inventory.domain.value_objects.quantity import Quantity
from inventory.domain.value_objects.source_identity import SourceIdentity
from inventory.domain.value_objects.stock_key import StockKey
from inventory.domain.value_objects.unit_cost import UnitCost


@dataclass(frozen=True, slots=True)
class StockOperationResult:
    """Operation movement identity plus the current tenant-scoped Stock state."""

    stock_key: StockKey
    current_quantity: Quantity
    current_average_cost: UnitCost
    movement_source_identity: SourceIdentity
    movement_type: MovementType
    direction: MovementDirection
    idempotent: bool
