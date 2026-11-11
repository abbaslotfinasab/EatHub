"""Composition wiring for Sales-triggered order reservation release."""

from inventory.application.context import InventoryExecutionContext
from inventory.application.use_cases.manage_reservations import ManageReservations
from inventory.infrastructure.django.reservation_repository import DjangoReservationRepository
from inventory.infrastructure.django.unit_of_work import DjangoInventoryUnitOfWork


def release_remaining_order_reservation(
    *, business_id: int, order_id: int, actor_id: int, reason: str
) -> None:
    """Delegate order-hold release to Inventory Application."""
    use_case = ManageReservations(
        DjangoReservationRepository(), DjangoInventoryUnitOfWork()
    )
    use_case.release_for_order(
        InventoryExecutionContext(business_id, actor_id), order_id, reason
    )
