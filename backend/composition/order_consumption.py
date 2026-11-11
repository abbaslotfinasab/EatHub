"""Composition wiring for the Inventory-owned order consumption use case."""

from inventory.application.context import InventoryExecutionContext
from inventory.application.use_cases.apply_order_consumption import ApplyOrderConsumption
from inventory.application.use_cases.manage_reservations import ManageReservations
from inventory.infrastructure.django.order_consumption_repository import (
    DjangoOrderConsumptionPostingRepository,
)
from inventory.infrastructure.django.reservation_repository import DjangoReservationRepository
from inventory.infrastructure.django.unit_of_work import DjangoInventoryUnitOfWork


def apply_order_consumption_inventory(
    *,
    business_id: int,
    order_id: int,
    actor_id: int,
    consumption_id: int,
    warehouse_id: int,
    reservation_id: int,
    remaining_lines: list[dict],
    actual_lines: list[dict],
) -> tuple[int, dict[int, int]]:
    """Wire Inventory adapters and execute its application-owned workflow."""
    unit_of_work = DjangoInventoryUnitOfWork()
    use_case = ApplyOrderConsumption(
        ManageReservations(DjangoReservationRepository(), unit_of_work),
        DjangoOrderConsumptionPostingRepository(),
        unit_of_work,
    )
    result = use_case.execute(
        InventoryExecutionContext(business_id, actor_id),
        order_id=order_id,
        consumption_id=consumption_id,
        warehouse_id=warehouse_id,
        reservation_id=reservation_id,
        remaining_lines=remaining_lines,
        actual_lines=actual_lines,
    )
    return result.operation_id, result.movement_ids_by_ingredient
