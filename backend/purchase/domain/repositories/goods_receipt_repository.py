from abc import ABC, abstractmethod
from datetime import datetime

from purchase.domain.entities.goods_receipt import GoodsReceipt


class GoodsReceiptRepository(ABC):

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
