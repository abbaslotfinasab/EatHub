from typing import Protocol

from inventory.application.context import InventoryExecutionContext
from inventory.application.dto.order_consumption_posting import OrderConsumptionPostingDTO


class OrderConsumptionPostingRepository(Protocol):
    def post_order_issue(
        self,
        context: InventoryExecutionContext,
        *,
        warehouse_id: int,
        order_id: int,
        consumption_id: int,
        lines: list[dict],
    ) -> OrderConsumptionPostingDTO:
        """Post the physical issue and return its tenant-scoped ledger identities."""
