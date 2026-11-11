from typing import Protocol

from inventory.domain.entities.reservation import ReservationLine


class OrderReservationSource(Protocol):
    """Sales-owned facts needed to validate an Inventory order reservation."""

    def is_active(self, business_id: int, order_id: int) -> bool: ...

    def reservation_matches(
        self, business_id: int, order_id: int, lines: list[ReservationLine]
    ) -> bool: ...
