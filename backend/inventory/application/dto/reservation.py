from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from inventory.domain.enums.reservation import ReservationStatus
from inventory.domain.value_objects.unit import Unit


@dataclass(frozen=True, slots=True)
class ReservationLineDTO:
    id: int
    ingredient_id: int
    ingredient_name: str
    source_line_id: int | None
    quantity: Decimal
    unit: Unit


@dataclass(frozen=True, slots=True)
class ReservationDTO:
    id: int
    business_id: int
    warehouse_id: int
    warehouse_name: str
    source_type: str
    source_id: int | None
    reason: str
    status: ReservationStatus
    idempotency_key: str
    payload_fingerprint: str
    created_by_id: int
    released_by_id: int | None
    released_at: datetime | None
    release_reason: str
    created_at: datetime
    updated_at: datetime
    lines: tuple[ReservationLineDTO, ...]


@dataclass(frozen=True, slots=True)
class StockAvailabilityDTO:
    business_id: int
    warehouse_id: int
    ingredient_id: int
    ingredient_name: str
    physical_quantity: Decimal
    reserved_quantity: Decimal
    available_quantity: Decimal
    unit: Unit
