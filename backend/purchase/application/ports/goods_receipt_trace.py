from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class StockMovementTraceRecord:
    id: int
    business_id: int
    source_type: str
    source_document_id: int
    source_line_id: int
    operation_kind: str
    movement_type: str
    direction: str
    quantity: Decimal
    unit: str
    unit_cost: Decimal
    occurred_at: datetime | None
    actor_id: int | None
    stock_id: int
    stock_business_id: int
    warehouse_id: int
    warehouse_name: str
    warehouse_business_id: int
    ingredient_id: int
    ingredient_name: str
    ingredient_business_id: int


@dataclass(frozen=True)
class GoodsReceiptMovementLinkRecord:
    receipt_id: int
    receipt_business_id: int
    received_date: datetime
    received_by_id: int
    receipt_purchase_order_id: int
    receipt_item_id: int
    purchase_order_item_id: int
    received_quantity: Decimal
    rejected_quantity: Decimal
    purchase_unit: str | None
    purchase_order_id: int
    purchase_order_business_id: int
    purchase_order_status: str
    supplier_id: int
    supplier_name: str
    supplier_business_id: int
    purchase_order_item_purchase_order_id: int
    purchase_order_item_ingredient_id: int
    purchase_order_item_quantity: Decimal
    purchase_order_item_purchase_unit: str
    purchase_order_item_unit_price: Decimal


class GoodsReceiptTraceReader(Protocol):
    def get_stock_movement_for_business(
        self, movement_id: int, business_id: int
    ) -> StockMovementTraceRecord | None:
        """Return a movement and its stock dimensions within a business."""

    def get_receipt_link_for_movement(
        self, movement_id: int, business_id: int
    ) -> GoodsReceiptMovementLinkRecord | None:
        """Return the linked receipt trace only when its receipt belongs to a business."""
