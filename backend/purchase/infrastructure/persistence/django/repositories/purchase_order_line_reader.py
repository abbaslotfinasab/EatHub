from purchase.application.ports.goods_receipt import PurchaseOrderLine
from purchase.models import PurchaseOrderItem as DjangoPurchaseOrderItem


class DjangoPurchaseOrderLineReader:
    def get_lines(
        self,
        purchase_order_id: int,
        business_id: int,
    ) -> dict[int, PurchaseOrderLine]:
        rows = DjangoPurchaseOrderItem.objects.filter(
            purchase_order_id=purchase_order_id,
            purchase_order__business_id=business_id,
            ingredient__business_id=business_id,
        ).values(
            "id",
            "ingredient_id",
            "quantity",
        ).order_by("id")

        return {
            row["id"]: PurchaseOrderLine(
                purchase_order_item_id=row["id"],
                ingredient_id=row["ingredient_id"],
                ordered_quantity=row["quantity"],
            )
            for row in rows
        }
