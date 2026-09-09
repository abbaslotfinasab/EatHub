# purchase/domain/entities/requisition.py

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from purchase.domain.enums.requisition_status import (
    RequisitionStatus,
)


@dataclass
class PurchaseRequisitionItem:
    ingredient_id: int
    quantity: Decimal
    note: str = ""

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError(
                "Requisition item quantity must be greater than zero."
            )

        if self.note:
            self.note = self.note.strip()


@dataclass
class PurchaseRequisition:
    id: int | None
    business_id: int
    requested_by_id: int

    status: RequisitionStatus = RequisitionStatus.DRAFT

    reason: str = ""

    items: list[PurchaseRequisitionItem] = field(
        default_factory=list
    )

    created_at: datetime | None = None
    updated_at: datetime | None = None

    # ------------------------------------------------------------------
    # Item management
    # ------------------------------------------------------------------

    def add_item(
        self,
        ingredient_id: int,
        quantity: Decimal,
        note: str = "",
    ) -> PurchaseRequisitionItem:

        if self.status != RequisitionStatus.DRAFT:
            raise ValueError(
                "Items can only be added to a draft requisition."
            )

        item = PurchaseRequisitionItem(
            ingredient_id=ingredient_id,
            quantity=quantity,
            note=note,
        )

        self.items.append(item)

        return item

    def remove_item(
        self,
        ingredient_id: int,
    ) -> None:

        if self.status != RequisitionStatus.DRAFT:
            raise ValueError(
                "Items can only be removed from a draft requisition."
            )

        original_count = len(self.items)

        self.items = [
            item
            for item in self.items
            if item.ingredient_id != ingredient_id
        ]

        if len(self.items) == original_count:
            raise ValueError(
                "Ingredient is not included in this requisition."
            )

    def clear_items(self) -> None:

        if self.status != RequisitionStatus.DRAFT:
            raise ValueError(
                "Items can only be cleared from a draft requisition."
            )

        self.items.clear()

    # ------------------------------------------------------------------
    # Status transitions
    # ------------------------------------------------------------------

    def submit(self) -> None:

        self._ensure_status(
            RequisitionStatus.DRAFT
        )

        self._ensure_has_items()

        self.status = RequisitionStatus.SUBMITTED

    def approve(self) -> None:

        self._ensure_status(
            RequisitionStatus.SUBMITTED
        )

        self.status = RequisitionStatus.APPROVED

    def reject(self) -> None:

        self._ensure_status(
            RequisitionStatus.SUBMITTED
        )

        self.status = RequisitionStatus.REJECTED

    def complete(self) -> None:

        self._ensure_status(
            RequisitionStatus.APPROVED
        )

        self.status = RequisitionStatus.COMPLETED

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def has_items(self) -> bool:
        return bool(self.items)

    def total_items(self) -> int:
        return len(self.items)

    def _ensure_has_items(self) -> None:

        if not self.items:
            raise ValueError(
                "Purchase requisition must contain at least one item."
            )

    def _ensure_status(
        self,
        expected_status: RequisitionStatus,
    ) -> None:

        if self.status != expected_status:
            raise ValueError(
                f"Invalid requisition status transition: "
                f"{self.status} -> {expected_status}."
            )