from purchase.domain.entities.goods_receipt import GoodsReceipt
from purchase.domain.repositories.goods_receipt_repository import (
    GoodsReceiptRepository,
)


class GetGoodsReceiptUseCase:
    def __init__(self, goods_receipt_repository: GoodsReceiptRepository) -> None:
        self._goods_receipt_repository = goods_receipt_repository

    def execute(self, goods_receipt_id: int, business_id: int) -> GoodsReceipt:
        goods_receipt_id = self._validate_positive_id(
            goods_receipt_id,
            "Goods receipt ID",
        )
        business_id = self._validate_positive_id(business_id, "Business ID")
        receipt = self._goods_receipt_repository.get_by_id_for_business(
            goods_receipt_id,
            business_id,
        )
        if receipt is None:
            raise ValueError("Goods receipt does not exist in this business.")
        return receipt

    @staticmethod
    def _validate_positive_id(value: int, field_name: str) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")
        return value
