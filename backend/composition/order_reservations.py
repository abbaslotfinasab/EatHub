"""Composition boundary for Sales-triggered order reservation release."""

from uuid import UUID, uuid5

from inventory.application.context import InventoryExecutionContext
from inventory.application.use_cases.manage_reservations import ManageReservations
from inventory.domain.enums.reservation import ReservationStatus
from inventory.domain.entities.reservation import ORDER_RESERVATION_SOURCE
from inventory.infrastructure.django.reservation_repository import DjangoReservationRepository
from inventory.infrastructure.django.unit_of_work import DjangoInventoryUnitOfWork


_ORDER_KEY_NAMESPACE = UUID("90144542-95ef-4eef-a498-0e73f429725d")


def release_remaining_order_reservation(
    *, business_id: int, order_id: int, actor_id: int, reason: str
) -> None:
    """Release the active reservation for an order within the caller's DB transaction."""
    use_case = ManageReservations(
        DjangoReservationRepository(), DjangoInventoryUnitOfWork()
    )
    context = InventoryExecutionContext(business_id, actor_id)
    _total, reservations = use_case.list(
        context,
        source_type=ORDER_RESERVATION_SOURCE,
        source_id=order_id,
        status=ReservationStatus.ACTIVE.value,
        page=1,
        page_size=100,
    )
    if not reservations:
        return

    active = reservations[0]
    use_case.release(
        context,
        active.id,
        uuid5(_ORDER_KEY_NAMESPACE, f"release:{active.id}"),
        reason,
    )
