from purchase.domain.entities.purchase_order import PurchaseOrder
from purchase.domain.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)


class GetPurchaseOrderUseCase:
    def __init__(self, purchase_order_repository: PurchaseOrderRepository) -> None:
        self._purchase_order_repository = purchase_order_repository

    def execute(self, purchase_order_id: int, business_id: int) -> PurchaseOrder:
        purchase_order_id = self._validate_positive_id(
            purchase_order_id,
            "Purchase order ID",
        )
        business_id = self._validate_positive_id(business_id, "Business ID")

        purchase_order = (
            self._purchase_order_repository.get_by_id_for_business(
                purchase_order_id,
                business_id,
            )
        )
        if purchase_order is None:
            raise ValueError("Purchase order does not exist in this business.")

        return purchase_order

    @staticmethod
    def _validate_positive_id(value: int, field_name: str) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")
        return value
