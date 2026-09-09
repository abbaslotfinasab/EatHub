from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from purchase.domain.enums.purchase_order_status import (
    PurchaseOrderStatus,
)


@dataclass(frozen=True)
class CreatePurchaseOrderItemDTO:
    ingredient_id: int
    quantity: Decimal
    unit_price: Decimal


@dataclass(frozen=True)
class CreatePurchaseOrderDTO:
    business_id: int
    supplier_id: int
    order_date: date
    items: list[CreatePurchaseOrderItemDTO]
    requisition_id: int | None = None
    expected_date: date | None = None
    discount: Decimal = Decimal("0")
    tax: Decimal = Decimal("0")


@dataclass(frozen=True)
class UpdatePurchaseOrderDTO:
    business_id: int
    purchase_order_id: int
    items: list[CreatePurchaseOrderItemDTO]
    discount: Decimal = Decimal("0")
    tax: Decimal = Decimal("0")


@dataclass(frozen=True)
class ListPurchaseOrdersQuery:
    business_id: int
    status: PurchaseOrderStatus | None = None
    supplier_id: int | None = None
    requisition_id: int | None = None
    order_date_from: date | None = None
    order_date_to: date | None = None
