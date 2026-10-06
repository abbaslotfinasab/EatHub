from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from purchase.domain.enums.purchase_invoice_status import PurchaseInvoiceStatus
from purchase.domain.enums.purchase_invoice_matching_status import PurchaseInvoiceMatchingStatus

MONEY_QUANTUM = Decimal("0.01")
ZERO = Decimal("0.00")


def money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


@dataclass
class PurchaseInvoiceItem:
    ingredient_id: int
    quantity: Decimal
    unit_price: Decimal
    purchase_order_item_id: int
    description: str = ""
    discount_percent: Decimal = ZERO
    tax_percent: Decimal = ZERO
    id: int | None = None

    def __post_init__(self) -> None:
        self.description = self.description.strip()
        self.validate()

    @property
    def line_subtotal(self) -> Decimal:
        return money(self.quantity * self.unit_price)

    @property
    def discount_amount(self) -> Decimal:
        return money(self.line_subtotal * self.discount_percent / Decimal("100"))

    @property
    def taxable_subtotal(self) -> Decimal:
        return money(self.line_subtotal - self.discount_amount)

    @property
    def tax_amount(self) -> Decimal:
        return money(self.taxable_subtotal * self.tax_percent / Decimal("100"))

    @property
    def total_price(self) -> Decimal:
        return money(self.taxable_subtotal + self.tax_amount)

    def validate(self) -> None:
        if not isinstance(self.purchase_order_item_id, int) or self.purchase_order_item_id <= 0:
            raise ValueError("Purchase order item ID must be a positive integer.")
        if self.ingredient_id <= 0:
            raise ValueError("Ingredient ID must be greater than zero.")
        if self.quantity <= 0:
            raise ValueError("Invoice item quantity must be greater than zero.")
        if self.unit_price < 0:
            raise ValueError("Invoice item unit price cannot be negative.")
        if self.discount_percent < 0 or self.discount_percent > 100:
            raise ValueError("Item discount percent must be between 0 and 100.")
        if self.tax_percent < 0:
            raise ValueError("Item tax percent cannot be negative.")


@dataclass
class PurchaseInvoice:
    id: int | None
    business_id: int
    supplier_id: int
    invoice_number: str
    invoice_date: date
    purchase_order_id: int | None
    discount_percent: Decimal = ZERO
    tax_percent: Decimal = ZERO
    items: list[PurchaseInvoiceItem] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    status: PurchaseInvoiceStatus = PurchaseInvoiceStatus.DRAFT
    approved_at: datetime | None = None
    approved_by_id: int | None = None
    posted_at: datetime | None = None
    posted_by_id: int | None = None
    matching_status: PurchaseInvoiceMatchingStatus = PurchaseInvoiceMatchingStatus.NOT_MATCHED
    matched_at: datetime | None = None

    def __post_init__(self) -> None:
        self.invoice_number = self.invoice_number.strip()
        try:
            self.status = PurchaseInvoiceStatus(self.status)
        except (TypeError, ValueError) as error:
            raise ValueError("Invalid purchase invoice status.") from error
        try:
            self.matching_status = PurchaseInvoiceMatchingStatus(self.matching_status)
        except (TypeError, ValueError) as error:
            raise ValueError("Invalid purchase invoice matching status.") from error
        self.validate()

    @property
    def subtotal(self) -> Decimal:
        return money(sum((item.line_subtotal for item in self.items), ZERO))

    @property
    def total_item_discount(self) -> Decimal:
        return money(sum((item.discount_amount for item in self.items), ZERO))

    @property
    def total_item_tax(self) -> Decimal:
        return money(sum((item.tax_amount for item in self.items), ZERO))

    @property
    def discount_amount(self) -> Decimal:
        return money(self.subtotal * self.discount_percent / Decimal("100"))

    @property
    def tax_amount(self) -> Decimal:
        taxable = money(
            self.subtotal
            - self.total_item_discount
            - self.discount_amount
        )
        return money(taxable * self.tax_percent / Decimal("100"))

    @property
    def total_price(self) -> Decimal:
        return money(
            self.subtotal
            - self.total_item_discount
            - self.discount_amount
            + self.total_item_tax
            + self.tax_amount
        )

    def add_item(self, ingredient_id: int, quantity: Decimal, unit_price: Decimal,
                 purchase_order_item_id: int,
                 description: str = "", discount_percent: Decimal = ZERO,
                 tax_percent: Decimal = ZERO) -> PurchaseInvoiceItem:
        self.ensure_editable()
        if any(item.purchase_order_item_id == purchase_order_item_id for item in self.items):
            raise ValueError("Purchase order item may only appear once in a purchase invoice.")
        item = PurchaseInvoiceItem(
            ingredient_id=ingredient_id,
            quantity=quantity,
            unit_price=unit_price,
            purchase_order_item_id=purchase_order_item_id,
            description=description,
            discount_percent=discount_percent,
            tax_percent=tax_percent,
        )
        self.items.append(item)
        return item

    def clear_items(self) -> None:
        self.ensure_editable()
        self.items.clear()

    def update_details(
        self,
        *,
        supplier_id: int,
        invoice_number: str,
        invoice_date: date,
        purchase_order_id: int,
        discount_percent: Decimal,
        tax_percent: Decimal,
        items: list[PurchaseInvoiceItem],
    ) -> None:
        self.ensure_editable()
        self.supplier_id = supplier_id
        self.invoice_number = invoice_number.strip()
        self.invoice_date = invoice_date
        self.purchase_order_id = purchase_order_id
        self.discount_percent = discount_percent
        self.tax_percent = tax_percent
        self.items = items
        self.validate()

    def approve(self, approved_by_id: int, approved_at: datetime) -> None:
        if self.status != PurchaseInvoiceStatus.DRAFT:
            raise ValueError(
                f"Purchase invoice cannot be approved from status '{self.status}'."
            )
        if not isinstance(approved_by_id, int) or approved_by_id <= 0:
            raise ValueError("Approval actor ID must be a positive integer.")
        if not isinstance(approved_at, datetime):
            raise ValueError("Approval timestamp is required.")
        self.status = PurchaseInvoiceStatus.APPROVED
        self.approved_by_id = approved_by_id
        self.approved_at = approved_at
        self.validate()

    def post(self, posted_by_id: int, posted_at: datetime) -> None:
        if self.status != PurchaseInvoiceStatus.APPROVED:
            raise ValueError(
                f"Purchase invoice cannot be posted from status '{self.status}'."
            )
        if not isinstance(posted_by_id, int) or posted_by_id <= 0:
            raise ValueError("Posting actor ID must be a positive integer.")
        if not isinstance(posted_at, datetime):
            raise ValueError("Posting timestamp is required.")
        self.status = PurchaseInvoiceStatus.POSTED
        self.posted_by_id = posted_by_id
        self.posted_at = posted_at
        self.validate()

    def ensure_editable(self) -> None:
        if self.status != PurchaseInvoiceStatus.DRAFT:
            raise ValueError("Only draft purchase invoices can be modified.")

    def validate(self) -> None:
        if not self.invoice_number:
            raise ValueError("Invoice number cannot be empty.")
        if self.business_id <= 0 or self.supplier_id <= 0:
            raise ValueError("Business and supplier IDs must be positive.")
        if self.purchase_order_id is None or self.purchase_order_id <= 0:
            raise ValueError("Purchase invoice must reference a purchase order.")
        if not self.items:
            raise ValueError("Purchase invoice must contain at least one item.")
        if self.discount_percent < 0 or self.discount_percent > 100:
            raise ValueError("Invoice discount percent must be between 0 and 100.")
        if self.tax_percent < 0:
            raise ValueError("Invoice tax percent cannot be negative.")
        po_item_ids = [item.purchase_order_item_id for item in self.items]
        if len(po_item_ids) != len(set(po_item_ids)):
            raise ValueError("Purchase order item may only appear once in a purchase invoice.")
        if self.status == PurchaseInvoiceStatus.DRAFT:
            if self.approved_at is not None or self.approved_by_id is not None:
                raise ValueError("Draft purchase invoice cannot have approval metadata.")
            if self.posted_at is not None or self.posted_by_id is not None:
                raise ValueError("Draft purchase invoice cannot have posting metadata.")
        elif self.status == PurchaseInvoiceStatus.APPROVED:
            if not isinstance(self.approved_by_id, int) or self.approved_by_id <= 0:
                raise ValueError("Approved purchase invoice requires an approval actor.")
            if not isinstance(self.approved_at, datetime):
                raise ValueError("Approved purchase invoice requires an approval timestamp.")
            if self.posted_at is not None or self.posted_by_id is not None:
                raise ValueError("Approved purchase invoice cannot have posting metadata.")
        elif self.status == PurchaseInvoiceStatus.POSTED:
            if not isinstance(self.approved_by_id, int) or self.approved_by_id <= 0:
                raise ValueError("Posted purchase invoice requires approval metadata.")
            if not isinstance(self.approved_at, datetime):
                raise ValueError("Posted purchase invoice requires approval metadata.")
            if not isinstance(self.posted_by_id, int) or self.posted_by_id <= 0:
                raise ValueError("Posted purchase invoice requires a posting actor.")
            if not isinstance(self.posted_at, datetime):
                raise ValueError("Posted purchase invoice requires a posting timestamp.")
        for item in self.items:
            item.validate()

    def validate_purchase_order_item_references(
        self,
        *,
        purchase_order_id: int,
        purchase_order_business_id: int,
        item_ingredient_ids: dict[int, int],
    ) -> None:
        if purchase_order_id != self.purchase_order_id:
            raise ValueError("Purchase order does not match the invoice purchase order.")
        if purchase_order_business_id != self.business_id:
            raise ValueError("Purchase order does not belong to the invoice business.")
        for item in self.items:
            ingredient_id = item_ingredient_ids.get(item.purchase_order_item_id)
            if ingredient_id is None:
                raise ValueError("Purchase order item does not belong to this purchase order and business.")
            if ingredient_id != item.ingredient_id:
                raise ValueError("Invoice item ingredient does not match its purchase order item.")
