from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class GoodsReceiptItem:
    purchase_order_item_id: int
    received_quantity: Decimal
    rejected_quantity: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if (
            not isinstance(self.purchase_order_item_id, int)
            or self.purchase_order_item_id <= 0
        ):
            raise ValueError(
                "Purchase order item ID must be a positive integer."
            )

        if self.received_quantity < 0:
            raise ValueError("Received quantity cannot be negative.")

        if self.rejected_quantity < 0:
            raise ValueError("Rejected quantity cannot be negative.")

        if self.received_quantity == 0 and self.rejected_quantity == 0:
            raise ValueError(
                "Received or rejected quantity must be greater than zero."
            )

    @property
    def accepted_quantity(self) -> Decimal:
        return self.received_quantity

    @property
    def total_processed_quantity(self) -> Decimal:
        return self.received_quantity + self.rejected_quantity

    @property
    def has_rejection(self) -> bool:
        return self.rejected_quantity > 0


@dataclass
class GoodsReceipt:
    id: int | None
    business_id: int
    purchase_order_id: int
    received_by_id: int
    received_date: datetime

    notes: str = ""
    items: list[GoodsReceiptItem] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.business_id, int) or self.business_id <= 0:
            raise ValueError("Business ID must be a positive integer.")

        if (
            not isinstance(self.purchase_order_id, int)
            or self.purchase_order_id <= 0
        ):
            raise ValueError("Purchase order ID must be a positive integer.")

        if not isinstance(self.received_by_id, int) or self.received_by_id <= 0:
            raise ValueError("Received by ID must be a positive integer.")

        self.notes = self.notes.strip()

    # ------------------------------------------------------------------
    # Item management
    # ------------------------------------------------------------------

    def add_item(
        self,
        purchase_order_item_id: int,
        received_quantity: Decimal,
        rejected_quantity: Decimal = Decimal("0"),
    ) -> GoodsReceiptItem:
        if self._has_purchase_order_item(purchase_order_item_id):
            raise ValueError(
                "This purchase order item already exists in the receipt."
            )

        item = GoodsReceiptItem(
            purchase_order_item_id=purchase_order_item_id,
            received_quantity=received_quantity,
            rejected_quantity=rejected_quantity,
        )
        self.items.append(item)

        return item

    def remove_item(self, purchase_order_item_id: int) -> None:
        original_count = len(self.items)
        self.items = [
            item
            for item in self.items
            if item.purchase_order_item_id != purchase_order_item_id
        ]

        if len(self.items) == original_count:
            raise ValueError(
                "Purchase order item is not included in this goods receipt."
            )

    def clear_items(self) -> None:
        self.items.clear()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> None:
        if not self.items:
            raise ValueError("Goods receipt must contain at least one item.")

        for item in self.items:
            self._validate_item(item)

        self._validate_duplicate_items()

    @staticmethod
    def _validate_item(item: GoodsReceiptItem) -> None:
        if item.received_quantity < 0:
            raise ValueError("Received quantity cannot be negative.")

        if item.rejected_quantity < 0:
            raise ValueError("Rejected quantity cannot be negative.")

        if item.received_quantity == 0 and item.rejected_quantity == 0:
            raise ValueError(
                "Received or rejected quantity must be greater than zero."
            )

    def _validate_duplicate_items(self) -> None:
        item_ids = [item.purchase_order_item_id for item in self.items]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError(
                "A purchase order item cannot appear more than once "
                "in the same goods receipt."
            )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def has_items(self) -> bool:
        return bool(self.items)

    def total_items(self) -> int:
        return len(self.items)

    @property
    def item_count(self) -> int:
        return self.total_items()

    @property
    def total_received_quantity(self) -> Decimal:
        return sum(
            (item.received_quantity for item in self.items),
            Decimal("0"),
        )

    @property
    def total_rejected_quantity(self) -> Decimal:
        return sum(
            (item.rejected_quantity for item in self.items),
            Decimal("0"),
        )

    @property
    def total_processed_quantity(self) -> Decimal:
        return sum(
            (item.total_processed_quantity for item in self.items),
            Decimal("0"),
        )

    @property
    def has_rejections(self) -> bool:
        return any(item.has_rejection for item in self.items)

    def _has_purchase_order_item(self, purchase_order_item_id: int) -> bool:
        return any(
            item.purchase_order_item_id == purchase_order_item_id
            for item in self.items
        )
