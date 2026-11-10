"""Composition boundary for posting actual order consumption to Inventory."""

from uuid import UUID, uuid5

from inventory.application.context import InventoryExecutionContext
from inventory.application.exceptions import InvalidApplicationInput
from inventory.application.use_cases.manage_reservations import ManageReservations
from inventory.infrastructure.django.models import (
    InventoryOperation,
    InventoryOperationLine,
    InventoryV1StockMovement,
)
from inventory.infrastructure.django.operations_service import (
    OperationInputError,
    create_operation,
    post_issue,
)
from inventory.infrastructure.django.reservation_repository import DjangoReservationRepository
from inventory.infrastructure.django.unit_of_work import DjangoInventoryUnitOfWork


_ORDER_KEY_NAMESPACE = UUID("90144542-95ef-4eef-a498-0e73f429725d")


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
    """Replace the reservation and post the actual stock issue atomically.

    The caller owns the outer order/consumption transaction. Inventory's nested
    atomic blocks join it, preserving rollback across the order event and ledger.
    Returns the operation ID and movement IDs keyed by ingredient ID.
    """
    context = InventoryExecutionContext(business_id, actor_id)
    reservations = ManageReservations(
        DjangoReservationRepository(), DjangoInventoryUnitOfWork()
    )
    reservations.release(
        context,
        reservation_id,
        uuid5(_ORDER_KEY_NAMESPACE, f"consume-release:{consumption_id}"),
        f"Replaced by consumption {consumption_id}",
    )
    if remaining_lines:
        reservations.create_for_order(
            context,
            warehouse_id=warehouse_id,
            order_id=order_id,
            reason=f"Order {order_id} remaining requirement after consumption {consumption_id}",
            idempotency_key=uuid5(_ORDER_KEY_NAMESPACE, f"consume-reserve:{consumption_id}"),
            lines=remaining_lines,
        )

    try:
        operation = create_operation(
            business_id=business_id,
            actor_id=actor_id,
            operation_type=InventoryOperation.Type.ISSUE,
            warehouse_id=warehouse_id,
            reference=f"Order {order_id}",
            reason=f"Actual consumption for order {order_id}",
            notes=f"OrderInventoryConsumption:{consumption_id}",
            lines=actual_lines,
        )
        post_issue(business_id=business_id, actor_id=actor_id, operation_id=operation.pk)
    except OperationInputError as error:
        raise InvalidApplicationInput(str(error)) from error

    movement_by_ingredient = {}
    for operation_line in InventoryOperationLine.objects.filter(
        operation=operation
    ).order_by("ingredient_id"):
        movement = InventoryV1StockMovement.objects.get(
            business_id=business_id,
            source_type="inventory_issue",
            source_document_id=operation.pk,
            source_line_id=operation_line.pk,
            operation_kind="post",
        )
        movement_by_ingredient[operation_line.ingredient_id] = movement.pk
    return operation.pk, movement_by_ingredient
