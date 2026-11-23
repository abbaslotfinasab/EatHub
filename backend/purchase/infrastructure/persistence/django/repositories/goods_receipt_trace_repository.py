from purchase.application.ports.goods_receipt_trace import (
    GoodsReceiptMovementLinkRecord,
    StockMovementTraceRecord,
)
from purchase.models import GoodsReceiptInventoryMovementLink
from inventory.infrastructure.django.models import InventoryV1StockMovement


class DjangoGoodsReceiptTraceRepository:
    """Django adapter for the Purchase-owned receipt trace read contract."""

    def get_stock_movement_for_business(
        self, movement_id: int, business_id: int
    ) -> StockMovementTraceRecord | None:
        movement = (
            InventoryV1StockMovement.objects.select_related(
                "stock__warehouse",
                "stock__ingredient",
            )
            .filter(pk=movement_id, business_id=business_id)
            .first()
        )
        if movement is None:
            return None
        stock = movement.stock
        return StockMovementTraceRecord(
            id=movement.pk,
            business_id=movement.business_id,
            source_type=movement.source_type,
            source_document_id=movement.source_document_id,
            source_line_id=movement.source_line_id,
            operation_kind=movement.operation_kind,
            movement_type=movement.movement_type,
            direction=movement.direction,
            quantity=movement.quantity,
            unit=movement.unit,
            unit_cost=movement.unit_cost,
            occurred_at=movement.occurred_at,
            actor_id=movement.actor_id,
            stock_id=stock.pk,
            stock_business_id=stock.business_id,
            warehouse_id=stock.warehouse_id,
            warehouse_name=stock.warehouse.name,
            warehouse_business_id=stock.warehouse.business_id,
            ingredient_id=stock.ingredient_id,
            ingredient_name=stock.ingredient.name,
            ingredient_business_id=stock.ingredient.business_id,
        )

    def get_receipt_link_for_movement(
        self, movement_id: int, business_id: int
    ) -> GoodsReceiptMovementLinkRecord | None:
        link = (
            GoodsReceiptInventoryMovementLink.objects.select_related(
                "receipt_item__receipt__purchase_order__supplier",
                "receipt_item__purchase_order_item__ingredient",
            )
            .filter(
                movement_id=movement_id,
                receipt_item__receipt__business_id=business_id,
            )
            .first()
        )
        if link is None:
            return None
        item = link.receipt_item
        receipt = item.receipt
        order = receipt.purchase_order
        order_item = item.purchase_order_item
        supplier = order.supplier
        return GoodsReceiptMovementLinkRecord(
            receipt_id=receipt.pk,
            receipt_business_id=receipt.business_id,
            received_date=receipt.received_date,
            received_by_id=receipt.received_by_id,
            receipt_purchase_order_id=receipt.purchase_order_id,
            receipt_item_id=item.pk,
            purchase_order_item_id=order_item.pk,
            received_quantity=item.received_quantity,
            rejected_quantity=item.rejected_quantity,
            purchase_unit=item.purchase_unit,
            purchase_order_id=order.pk,
            purchase_order_business_id=order.business_id,
            purchase_order_status=order.status,
            supplier_id=supplier.pk,
            supplier_name=supplier.name,
            supplier_business_id=supplier.business_id,
            purchase_order_item_purchase_order_id=order_item.purchase_order_id,
            purchase_order_item_ingredient_id=order_item.ingredient_id,
            purchase_order_item_quantity=order_item.quantity,
            purchase_order_item_purchase_unit=order_item.purchase_unit,
            purchase_order_item_unit_price=order_item.unit_price,
        )
