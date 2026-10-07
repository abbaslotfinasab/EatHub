from purchase.application.ports.goods_receipt import TransactionManager
from purchase.domain.entities.purchase_order import PurchaseOrder
from purchase.domain.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)


class CancelPurchaseOrderUseCase:
    def __init__(
        self,
        purchase_order_repository: PurchaseOrderRepository,
        transaction_manager: TransactionManager,
    ) -> None:
        self._purchase_order_repository = purchase_order_repository
        self._transaction_manager = transaction_manager

    def execute(self, purchase_order_id: int, business_id: int) -> PurchaseOrder:
        with self._transaction_manager.atomic():
            purchase_order = self._get_purchase_order_for_business(
                purchase_order_id,
                business_id,
                for_update=True,
            )
            purchase_order.cancel()

            return self._purchase_order_repository.save(purchase_order)

    def _get_purchase_order_for_business(
        self,
        purchase_order_id: int,
        business_id: int,
        *,
        for_update: bool = False,
    ) -> PurchaseOrder:
        purchase_order_id = self._validate_positive_id(
            purchase_order_id,
            "Purchase order ID",
        )
        business_id = self._validate_positive_id(business_id, "Business ID")
        loader = (
            self._purchase_order_repository.get_by_id_for_business_for_update
            if for_update
            else self._purchase_order_repository.get_by_id_for_business
        )
        purchase_order = loader(
            purchase_order_id,
            business_id,
        )
        if purchase_order is None:
            raise ValueError("Purchase order does not exist in this business.")

        return purchase_order

    @staticmethod
    def _validate_positive_id(value: int, field_name: str) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")
        return value
