from contextlib import AbstractContextManager
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from purchase.domain.enums.purchase_unit import PurchaseUnit


@dataclass(frozen=True)
class PurchaseOrderLine:
    purchase_order_item_id: int
    ingredient_id: int
    ordered_quantity: Decimal
    purchase_unit: PurchaseUnit | None
    unit_price: Decimal


class PurchaseOrderLineReader(Protocol):
    def get_lines(
        self,
        purchase_order_id: int,
        business_id: int,
    ) -> dict[int, PurchaseOrderLine]:
        """Return line projections scoped to the purchase order and business."""


@dataclass(frozen=True)
class InventoryReceiptRequest:
    """Purchase-owned receipt data with explicit quantity and price basis.

    ``unit_cost_amount`` is the Purchase Order line price per one
    ``unit_cost_unit`` in the Business accounting currency. Inventory owns
    normalization to the Ingredient's canonical unit.
    """

    business_id: int
    ingredient_id: int
    warehouse_id: int | None
    quantity_amount: Decimal
    quantity_unit: PurchaseUnit
    unit_cost_amount: Decimal
    unit_cost_unit: PurchaseUnit
    source_document_id: int
    source_line_id: int
    operation_kind: str
    actor_id: int


class InventoryReceiptGateway(Protocol):
    def receive_line(self, request: InventoryReceiptRequest) -> None:
        """Execute one Inventory receipt inside the caller's transaction."""


class TransactionManager(Protocol):
    def atomic(self) -> AbstractContextManager[None]:
        """Return a context manager covering the complete workflow."""
