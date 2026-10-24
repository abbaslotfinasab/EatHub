from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from purchase.domain.entities.goods_receipt import GoodsReceipt


class GoodsReceiptRepository(ABC):

    @abstractmethod
    def get_by_idempotency_key_for_business(
        self,
        idempotency_key: UUID,
        business_id: int,
    ) -> GoodsReceipt | None:
        """Return a keyed receipt only within the specified business."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id_for_business(
        self,
        goods_receipt_id: int,
        business_id: int,
    ) -> GoodsReceipt | None:
        """Return a goods receipt, including its items, within a business."""
        raise NotImplementedError

    @abstractmethod
    def list(
        self,
        business_id: int,
        *,
        purchase_order_id: int | None = None,
        received_by_id: int | None = None,
        received_from: datetime | None = None,
        received_to: datetime | None = None,
    ) -> list[GoodsReceipt]:
        """Return goods receipts belonging to a business."""
        raise NotImplementedError

    @abstractmethod
    def save(
        self,
        goods_receipt: GoodsReceipt,
    ) -> GoodsReceipt:
        """Create or update a goods receipt together with its items."""
        raise NotImplementedError
