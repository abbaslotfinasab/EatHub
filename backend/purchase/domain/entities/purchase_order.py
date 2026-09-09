from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from purchase.domain.enums.purchase_order_status import (
    PurchaseOrderStatus,
)


@dataclass
class PurchaseOrderItem:
    ingredient_id: int
    quantity: Decimal
    unit_price: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.ingredient_id, int) or self.ingredient_id <= 0:
            raise ValueError("Ingredient ID must be a positive integer.")

        if self.quantity <= 0:
            raise ValueError(
                "Purchase order item quantity must be greater than zero."
            )

        if self.unit_price < 0:
            raise ValueError(
                "Purchase order item unit price cannot be negative."
            )

    @property
    def line_total(self) -> Decimal:
        return self.quantity * self.unit_price

    @property
    def total_price(self) -> Decimal:
        return self.line_total


@dataclass
class PurchaseOrder:
    id: int | None
    business_id: int
    supplier_id: int
    order_date: date

    expected_date: date | None = None
    requisition_id: int | None = None
    status: PurchaseOrderStatus = PurchaseOrderStatus.DRAFT
    discount: Decimal = Decimal("0")
    tax: Decimal = Decimal("0")
    items: list[PurchaseOrderItem] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.business_id, int) or self.business_id <= 0:
            raise ValueError("Business ID must be a positive integer.")

        if not isinstance(self.supplier_id, int) or self.supplier_id <= 0:
            raise ValueError("Supplier ID must be a positive integer.")

        if self.requisition_id is not None and (
            not isinstance(self.requisition_id, int)
            or self.requisition_id <= 0
        ):
            raise ValueError("Requisition ID must be a positive integer.")

        self._validate_discount()
        self._validate_tax()

        if self.discount > self.subtotal:
            raise ValueError("Discount cannot exceed subtotal.")

    # ------------------------------------------------------------------
    # Amounts
    # ------------------------------------------------------------------

    @property
    def subtotal(self) -> Decimal:
        return sum((item.line_total for item in self.items), Decimal("0"))

    @property
    def total(self) -> Decimal:
        return self.subtotal - self.discount + self.tax

    def total_amount(self) -> Decimal:
        return self.total

    # ------------------------------------------------------------------
    # Item management
    # ------------------------------------------------------------------

    def add_item(
        self,
        ingredient_id: int,
        quantity: Decimal,
        unit_price: Decimal,
    ) -> PurchaseOrderItem:
        self._ensure_editable()

        item = PurchaseOrderItem(
            ingredient_id=ingredient_id,
            quantity=quantity,
            unit_price=unit_price,
        )
        self.items.append(item)

        return item

    def remove_item(self, ingredient_id: int) -> None:
        self._ensure_editable()

        original_count = len(self.items)
        self.items = [
            item for item in self.items if item.ingredient_id != ingredient_id
        ]

        if len(self.items) == original_count:
            raise ValueError(
                "Ingredient is not included in this purchase order."
            )

        if self.discount > self.subtotal:
            self.discount = self.subtotal

    def clear_items(self) -> None:
        self._ensure_editable()
        self.items.clear()
        self.discount = Decimal("0")

    def set_discount(self, discount: Decimal) -> None:
        self._ensure_editable()

        if discount < 0:
            raise ValueError("Discount cannot be negative.")

        if discount > self.subtotal:
            raise ValueError("Discount cannot exceed subtotal.")

        self.discount = discount

    def set_tax(self, tax: Decimal) -> None:
        self._ensure_editable()

        if tax < 0:
            raise ValueError("Tax cannot be negative.")

        self.tax = tax

    # ------------------------------------------------------------------
    # Status transitions
    # ------------------------------------------------------------------

    def send(self) -> None:
        self._ensure_status(PurchaseOrderStatus.DRAFT)
        self._ensure_has_items()
        self.status = PurchaseOrderStatus.SENT

    def submit(self) -> None:
        self.send()

    def mark_partially_received(self) -> None:
        self._ensure_status(PurchaseOrderStatus.SENT)
        self.status = PurchaseOrderStatus.PARTIAL

    def mark_received(self) -> None:
        if self.status not in (
            PurchaseOrderStatus.SENT,
            PurchaseOrderStatus.PARTIAL,
        ):
            raise ValueError(
                f"Purchase order cannot be received from status '{self.status}'."
            )

        self.status = PurchaseOrderStatus.RECEIVED

    def cancel(self) -> None:
        if self.status in (
            PurchaseOrderStatus.RECEIVED,
            PurchaseOrderStatus.CANCELLED,
        ):
            raise ValueError(
                f"Purchase order cannot be cancelled from status '{self.status}'."
            )

        self.status = PurchaseOrderStatus.CANCELLED

    # ------------------------------------------------------------------
    # Queries and helpers
    # ------------------------------------------------------------------

    def has_items(self) -> bool:
        return bool(self.items)

    def _ensure_editable(self) -> None:
        if self.status != PurchaseOrderStatus.DRAFT:
            raise ValueError(
                "Purchase order can only be modified while it is in draft status."
            )

    def _ensure_has_items(self) -> None:
        if not self.items:
            raise ValueError("Purchase order must contain at least one item.")

    def _ensure_status(self, expected_status: PurchaseOrderStatus) -> None:
        if self.status != expected_status:
            raise ValueError(
                f"Invalid purchase order status transition: "
                f"{self.status} -> {expected_status}."
            )

    def _validate_discount(self) -> None:
        if self.discount < 0:
            raise ValueError("Discount cannot be negative.")

    def _validate_tax(self) -> None:
        if self.tax < 0:
            raise ValueError("Tax cannot be negative.")
