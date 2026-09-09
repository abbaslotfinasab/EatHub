from datetime import datetime

from purchase.application.dto.goods_receipt import ListGoodsReceiptsQuery
from purchase.domain.entities.goods_receipt import GoodsReceipt
from purchase.domain.repositories.goods_receipt_repository import (
    GoodsReceiptRepository,
)


class ListGoodsReceiptsUseCase:
    def __init__(self, goods_receipt_repository: GoodsReceiptRepository) -> None:
        self._goods_receipt_repository = goods_receipt_repository

    def execute(self, query: ListGoodsReceiptsQuery) -> list[GoodsReceipt]:
        business_id = self._validate_positive_id(query.business_id, "Business ID")
        purchase_order_id = self._validate_optional_positive_id(
            query.purchase_order_id,
            "Purchase order ID",
        )
        received_by_id = self._validate_optional_positive_id(
            query.received_by_id,
            "Received by ID",
        )
        received_from = self._validate_optional_datetime(
            query.received_from,
            "Received from",
        )
        received_to = self._validate_optional_datetime(
            query.received_to,
            "Received to",
        )
        if received_from and received_to and received_from > received_to:
            raise ValueError("Received from cannot be after received to.")

        return self._goods_receipt_repository.list(
            business_id,
            purchase_order_id=purchase_order_id,
            received_by_id=received_by_id,
            received_from=received_from,
            received_to=received_to,
        )

    @staticmethod
    def _validate_positive_id(value: int, field_name: str) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")
        return value

    @classmethod
    def _validate_optional_positive_id(
        cls,
        value: int | None,
        field_name: str,
    ) -> int | None:
        if value is None:
            return None
        return cls._validate_positive_id(value, field_name)

    @staticmethod
    def _validate_optional_datetime(
        value: datetime | None,
        field_name: str,
    ) -> datetime | None:
        if value is not None and not isinstance(value, datetime):
            raise ValueError(f"{field_name} must be a datetime or None.")
        return value
