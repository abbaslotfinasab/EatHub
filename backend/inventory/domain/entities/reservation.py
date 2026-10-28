from dataclasses import dataclass
import re

from inventory.domain.enums.reservation import ReservationStatus
from inventory.domain.exceptions import InvalidReservation
from inventory.domain.value_objects.quantity import Quantity


_SOURCE_TYPE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
MANUAL_RESERVATION_SOURCE = "manual"
ORDER_RESERVATION_SOURCE = "order"


@dataclass(frozen=True, slots=True)
class ReservationLine:
    ingredient_id: int
    quantity: Quantity
    source_line_id: int | None = None

    def __post_init__(self) -> None:
        if isinstance(self.ingredient_id, bool) or not isinstance(self.ingredient_id, int) or self.ingredient_id <= 0:
            raise InvalidReservation("Ingredient ID must be a positive integer.")
        if not isinstance(self.quantity, Quantity) or self.quantity.amount <= 0:
            raise InvalidReservation("Reservation quantity must be positive.")


@dataclass(frozen=True, slots=True)
class ReservationRequest:
    business_id: int
    warehouse_id: int
    source_type: str
    source_id: int | None
    reason: str
    idempotency_key: str
    lines: tuple[ReservationLine, ...]

    def __post_init__(self) -> None:
        for value, label in ((self.business_id, "Business"), (self.warehouse_id, "Warehouse")):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise InvalidReservation(f"{label} ID must be a positive integer.")
        if not isinstance(self.source_type, str) or not _SOURCE_TYPE.fullmatch(self.source_type):
            raise InvalidReservation("Source type must be a lowercase identifier.")
        if self.source_type == MANUAL_RESERVATION_SOURCE:
            if self.source_id is not None or any(line.source_line_id is not None for line in self.lines):
                raise InvalidReservation("Manual reservations cannot reference external source IDs.")
        elif self.source_type == ORDER_RESERVATION_SOURCE:
            if isinstance(self.source_id, bool) or not isinstance(self.source_id, int) or self.source_id <= 0:
                raise InvalidReservation("Order reservations require a positive order ID.")
            if any(line.source_line_id is not None for line in self.lines):
                raise InvalidReservation("Order reservation lines are aggregated by ingredient.")
        else:
            raise InvalidReservation("Unsupported reservation source type.")
        if not isinstance(self.reason, str) or not self.reason.strip() or len(self.reason.strip()) > 500:
            raise InvalidReservation("A reservation reason of 1 to 500 characters is required.")
        if not isinstance(self.idempotency_key, str) or not self.idempotency_key.strip():
            raise InvalidReservation("An idempotency key is required.")
        if not self.lines:
            raise InvalidReservation("At least one reservation line is required.")

        unkeyed_ingredients = [line.ingredient_id for line in self.lines]
        if len(unkeyed_ingredients) != len(set(unkeyed_ingredients)):
            raise InvalidReservation("An ingredient may appear only once when source line IDs are omitted.")


def release_reservation(status: ReservationStatus) -> ReservationStatus:
    if status is not ReservationStatus.ACTIVE:
        raise InvalidReservation("Only an active reservation can be released.")
    return ReservationStatus.RELEASED
