from dataclasses import dataclass
from datetime import date
from datetime import datetime
from decimal import Decimal


@dataclass
class CreatePurchaseInvoiceItemDTO:
    ingredient_id: int
    quantity: Decimal
    unit_price: Decimal
    description: str = ""
    discount_percent: Decimal = Decimal("0")
    tax_percent: Decimal = Decimal("0")


@dataclass
class CreatePurchaseInvoiceDTO:
    business_id: int
    supplier_id: int
    purchase_order_id: int
    invoice_number: str
    invoice_date: date
    items: list[CreatePurchaseInvoiceItemDTO]
    discount_percent: Decimal = Decimal("0")
    tax_percent: Decimal = Decimal("0")


@dataclass(frozen=True)
class UpdatePurchaseInvoiceDTO:
    business_id: int
    purchase_invoice_id: int
    supplier_id: int
    purchase_order_id: int
    invoice_number: str
    invoice_date: date
    items: list[CreatePurchaseInvoiceItemDTO]
    discount_percent: Decimal = Decimal("0")
    tax_percent: Decimal = Decimal("0")


@dataclass(frozen=True)
class ApprovePurchaseInvoiceDTO:
    business_id: int
    purchase_invoice_id: int
    approved_by_id: int
    approved_at: datetime


@dataclass
class ListPurchaseInvoicesQuery:
    business_id: int
    supplier_id: int | None = None
    purchase_order_id: int | None = None
    invoice_date_from: date | None = None
    invoice_date_to: date | None = None
