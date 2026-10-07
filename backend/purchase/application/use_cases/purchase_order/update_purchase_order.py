from decimal import Decimal

from purchase.application.ports.goods_receipt import TransactionManager
from purchase.application.dto.purchase_order import UpdatePurchaseOrderDTO
from purchase.domain.entities.purchase_order import (
    PurchaseOrder,
    PurchaseOrderItem,
)
from purchase.domain.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)


class UpdatePurchaseOrderUseCase:
    def __init__(
        self,
        purchase_order_repository: PurchaseOrderRepository,
        transaction_manager: TransactionManager,
    ) -> None:
        self._purchase_order_repository = purchase_order_repository
        self._transaction_manager = transaction_manager

    def execute(self, command: UpdatePurchaseOrderDTO) -> PurchaseOrder:
        business_id = self._validate_positive_id(command.business_id, "Business ID")
        purchase_order_id = self._validate_positive_id(
            command.purchase_order_id,
            "Purchase order ID",
        )
        items = self._create_items(command.items)
        discount = self._validate_decimal(command.discount, "Discount")
        tax = self._validate_decimal(command.tax, "Tax")

        with self._transaction_manager.atomic():
            purchase_order = (
                self._purchase_order_repository.get_by_id_for_business_for_update(
                    purchase_order_id,
                    business_id,
                )
            )
            if purchase_order is None:
                raise ValueError("Purchase order does not exist in this business.")

            purchase_order.clear_items()
            for item in items:
                purchase_order.add_item(
                    item.ingredient_id,
                    item.quantity,
                    item.unit_price,
                )
            purchase_order.set_discount(discount)
            purchase_order.set_tax(tax)

            return self._purchase_order_repository.save(purchase_order)

    @staticmethod
    def _create_items(commands: list) -> list[PurchaseOrderItem]:
        return [
            PurchaseOrderItem(
                ingredient_id=item.ingredient_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            for item in commands
        ]

    @staticmethod
    def _validate_positive_id(value: int, field_name: str) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")
        return value

    @staticmethod
    def _validate_decimal(value: Decimal, field_name: str) -> Decimal:
        if not isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be a decimal.")
        return value
