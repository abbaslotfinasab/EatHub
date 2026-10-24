from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from purchase.domain.enums.purchase_unit import PurchaseUnit
from purchase.domain.entities.goods_receipt import GoodsReceipt


@dataclass(frozen=True)
class CreateGoodsReceiptItemDTO:
    purchase_order_item_id: int
    received_quantity: Decimal
    purchase_unit: PurchaseUnit
    rejected_quantity: Decimal = Decimal("0")


@dataclass(frozen=True)
class CreateGoodsReceiptDTO:
    business_id: int
    purchase_order_id: int
    received_by_id: int
    received_date: datetime
    items: list[CreateGoodsReceiptItemDTO]
    idempotency_key: UUID
    notes: str = ""
    warehouse_id: int | None = None


@dataclass(frozen=True)
class GoodsReceiptCreationResult:
    receipt: GoodsReceipt
    replayed: bool


@dataclass(frozen=True)
class ListGoodsReceiptsQuery:
    business_id: int
    purchase_order_id: int | None = None
    received_by_id: int | None = None
    received_from: datetime | None = None
    received_to: datetime | None = None
