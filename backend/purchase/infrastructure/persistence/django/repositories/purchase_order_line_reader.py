from purchase.application.ports.goods_receipt import PurchaseOrderLine
from purchase.domain.enums.purchase_unit import PurchaseUnit
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
            "purchase_unit",
            "unit_price",
        ).order_by("id")

        return {
            row["id"]: PurchaseOrderLine(
                purchase_order_item_id=row["id"],
                ingredient_id=row["ingredient_id"],
                ordered_quantity=row["quantity"],
                purchase_unit=(
                    PurchaseUnit(row["purchase_unit"])
                    if row["purchase_unit"] is not None else None
                ),
                unit_price=row["unit_price"],
            )
            for row in rows
        }
