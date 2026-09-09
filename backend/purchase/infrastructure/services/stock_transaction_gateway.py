from decimal import Decimal

from inventory.models import (
    Ingredient,
    Stock,
    StockTransaction,
    Warehouse,
)
from purchase.application.ports.goods_receipt import (
    StockInRequest,
    StockTransactionGateway,
)
from purchase.models import PurchaseOrderItem as DjangoPurchaseOrderItem


class DjangoStockTransactionGateway(StockTransactionGateway):
    REFERENCE_TYPE = "goods_receipt"

    def create_stock_in(self, request: StockInRequest) -> None:
        if request.quantity <= 0:
            return

        purchase_order_item = self._get_purchase_order_item(request)

        ingredient = Ingredient.objects.filter(
            id=request.ingredient_id,
            business_id=request.business_id,
        ).first()
        if ingredient is None:
            raise ValueError(
                "Ingredient does not exist in the stock transaction business."
            )

        warehouse = self._get_active_default_warehouse(request.business_id)

        stock = Stock.objects.select_for_update().filter(
            warehouse_id=warehouse.id,
            ingredient_id=ingredient.id,
        ).first()
        if stock is None:
            stock = Stock.objects.create(
                warehouse=warehouse,
                ingredient=ingredient,
                quantity=Decimal("0"),
            )

        stock.quantity += request.quantity
        stock.save(update_fields=["quantity", "updated_at"])

        StockTransaction.objects.create(
            stock=stock,
            quantity=request.quantity,
            unit_cost=purchase_order_item.unit_price,
            type=StockTransaction.Type.PURCHASE_RECEIVE,
            balance_after=stock.quantity,
            reference_type=self.REFERENCE_TYPE,
            reference_id=request.goods_receipt_id,
        )

    @staticmethod
    def _get_purchase_order_item(
        request: StockInRequest,
    ) -> DjangoPurchaseOrderItem:
        purchase_order_item = DjangoPurchaseOrderItem.objects.filter(
            id=request.purchase_order_item_id,
            purchase_order_id=request.purchase_order_id,
            purchase_order__business_id=request.business_id,
            ingredient_id=request.ingredient_id,
        ).first()
        if purchase_order_item is None:
            raise ValueError(
                "Purchase order item does not belong to the requested business."
            )
        return purchase_order_item

    @staticmethod
    def _get_active_default_warehouse(business_id: int) -> Warehouse:
        warehouses = list(
            Warehouse.objects.filter(
                business_id=business_id,
                is_active=True,
                is_default=True,
            ).order_by("id")[:2]
        )
        if not warehouses:
            raise ValueError(
                "An active default warehouse is required for stock receipt."
            )
        if len(warehouses) > 1:
            raise ValueError(
                "Multiple active default warehouses exist for this business."
            )
        return warehouses[0]
