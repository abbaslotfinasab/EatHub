from contextlib import AbstractContextManager
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class PurchaseOrderLine:
    purchase_order_item_id: int
    ingredient_id: int
    ordered_quantity: Decimal


class PurchaseOrderLineReader(Protocol):
    def get_lines(
        self,
        purchase_order_id: int,
        business_id: int,
    ) -> dict[int, PurchaseOrderLine]:
        """Return line projections scoped to the purchase order and business."""


@dataclass(frozen=True)
class StockInRequest:
    business_id: int
    purchase_order_id: int
    goods_receipt_id: int | None
    purchase_order_item_id: int
    ingredient_id: int
    quantity: Decimal


class StockTransactionGateway(Protocol):
    def create_stock_in(self, request: StockInRequest) -> None:
        """Persist one stock-in operation in the caller's transaction."""


class TransactionManager(Protocol):
    def atomic(self) -> AbstractContextManager[None]:
        """Return a context manager covering the complete workflow."""
