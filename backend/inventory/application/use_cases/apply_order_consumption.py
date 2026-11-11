from uuid import UUID, uuid5

from inventory.application.context import InventoryExecutionContext
from inventory.application.dto.order_consumption_posting import OrderConsumptionPostingDTO
from inventory.application.exceptions import InvalidApplicationInput
from inventory.application.ports.order_consumption import OrderConsumptionPostingRepository
from inventory.application.use_cases.manage_reservations import ManageReservations


_ORDER_KEY_NAMESPACE = UUID("90144542-95ef-4eef-a498-0e73f429725d")


class ApplyOrderConsumption:
    """Atomically replace an order hold and post its actual stock issue."""

    def __init__(
        self,
        reservations: ManageReservations,
        posting: OrderConsumptionPostingRepository,
    ) -> None:
        self._reservations = reservations
        self._posting = posting

    def execute(
        self,
        context: InventoryExecutionContext,
        *,
        order_id: int,
        consumption_id: int,
        warehouse_id: int,
        reservation_id: int,
        remaining_lines: list[dict],
        actual_lines: list[dict],
    ) -> OrderConsumptionPostingDTO:
        if not isinstance(context, InventoryExecutionContext) or context.actor_id is None:
            raise InvalidApplicationInput("A trusted inventory execution context is required.")
        for name, value in (
            ("order_id", order_id),
            ("consumption_id", consumption_id),
            ("warehouse_id", warehouse_id),
            ("reservation_id", reservation_id),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise InvalidApplicationInput(f"{name} must be a positive integer.")
        if not isinstance(remaining_lines, list) or not isinstance(actual_lines, list) or not actual_lines:
            raise InvalidApplicationInput("Actual consumption requires at least one posting line.")
        if any(not isinstance(line, dict) for line in remaining_lines + actual_lines):
            raise InvalidApplicationInput("Consumption lines must be objects.")

        self._reservations.release(
            context,
            reservation_id,
            uuid5(_ORDER_KEY_NAMESPACE, f"consume-release:{consumption_id}"),
            f"Replaced by consumption {consumption_id}",
        )
        if remaining_lines:
            self._reservations.create_for_order(
                context,
                warehouse_id=warehouse_id,
                order_id=order_id,
                reason=f"Order {order_id} remaining requirement after consumption {consumption_id}",
                idempotency_key=uuid5(_ORDER_KEY_NAMESPACE, f"consume-reserve:{consumption_id}"),
                lines=remaining_lines,
            )
        return self._posting.post_order_issue(
            context,
            warehouse_id=warehouse_id,
            order_id=order_id,
            consumption_id=consumption_id,
            lines=actual_lines,
        )
