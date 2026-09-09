from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class CreateGoodsReceiptItemDTO:
    purchase_order_item_id: int
    received_quantity: Decimal
    rejected_quantity: Decimal = Decimal("0")


@dataclass(frozen=True)
class CreateGoodsReceiptDTO:
    business_id: int
    purchase_order_id: int
    received_by_id: int
    received_date: datetime
    items: list[CreateGoodsReceiptItemDTO]
    notes: str = ""


@dataclass(frozen=True)
class ListGoodsReceiptsQuery:
    business_id: int
    purchase_order_id: int | None = None
    received_by_id: int | None = None
    received_from: datetime | None = None
    received_to: datetime | None = None
