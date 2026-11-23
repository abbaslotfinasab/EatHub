from purchase.application.exceptions import GoodsReceiptTraceUnavailable
from purchase.application.ports.goods_receipt_trace import (
    GoodsReceiptMovementLinkRecord,
    GoodsReceiptTraceReader,
    StockMovementTraceRecord,
)


class TraceGoodsReceiptStockMovementUseCase:
    def __init__(self, reader: GoodsReceiptTraceReader) -> None:
        self._reader = reader

    def execute(self, movement_id: int, business_id: int) -> dict:
        self._validate_positive_id(movement_id, "Stock movement ID")
        self._validate_positive_id(business_id, "Business ID")

        movement = self._reader.get_stock_movement_for_business(
            movement_id, business_id
        )
        if movement is None:
            raise ValueError("Stock movement does not exist in this business.")
        if (
            movement.source_type != "goods_receipt"
            or movement.movement_type != "receipt"
        ):
            raise ValueError(
                "The requested StockMovement is not a goods receipt movement."
            )

        link = self._reader.get_receipt_link_for_movement(
            movement.id, business_id
        )
        if link is None:
            raise GoodsReceiptTraceUnavailable(
                "This historical receipt movement has no verified receipt-line link."
            )
        self._validate_consistency(movement, link, business_id)

        return {
            "movement": {
                "id": movement.id,
                "business_id": movement.business_id,
                "source_type": movement.source_type,
                "source_document_id": movement.source_document_id,
                "source_line_id": movement.source_line_id,
                "operation_kind": movement.operation_kind,
                "movement_type": movement.movement_type,
                "direction": movement.direction,
                "quantity": movement.quantity,
                "unit": movement.unit,
                "unit_cost": movement.unit_cost,
                "occurred_at": movement.occurred_at,
                "actor_id": movement.actor_id,
                "stock_id": movement.stock_id,
                "warehouse_id": movement.warehouse_id,
                "warehouse_name": movement.warehouse_name,
                "ingredient_id": movement.ingredient_id,
                "ingredient_name": movement.ingredient_name,
            },
            "goods_receipt": {
                "id": link.receipt_id,
                "business_id": link.receipt_business_id,
                "received_date": link.received_date,
                "received_by_id": link.received_by_id,
                "purchase_order_id": link.receipt_purchase_order_id,
            },
            "goods_receipt_item": {
                "id": link.receipt_item_id,
                "purchase_order_item_id": link.purchase_order_item_id,
                "received_quantity": link.received_quantity,
                "rejected_quantity": link.rejected_quantity,
                "purchase_unit": link.purchase_unit,
            },
            "purchase_order": {
                "id": link.purchase_order_id,
                "status": link.purchase_order_status,
                "supplier_id": link.supplier_id,
                "supplier_name": link.supplier_name,
            },
            "purchase_order_item": {
                "id": link.purchase_order_item_id,
                "ingredient_id": link.purchase_order_item_ingredient_id,
                "ordered_quantity": link.purchase_order_item_quantity,
                "purchase_unit": link.purchase_order_item_purchase_unit,
                "unit_price": link.purchase_order_item_unit_price,
            },
            "supplier": {
                "id": link.supplier_id,
                "name": link.supplier_name,
            },
        }

    @staticmethod
    def _validate_positive_id(value: int, field_name: str) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")

    @staticmethod
    def _validate_consistency(
        movement: StockMovementTraceRecord,
        link: GoodsReceiptMovementLinkRecord,
        business_id: int,
    ) -> None:
        if (
            movement.business_id != business_id
            or movement.stock_business_id != business_id
            or movement.warehouse_business_id != business_id
            or movement.ingredient_business_id != business_id
            or link.receipt_business_id != business_id
            or link.purchase_order_business_id != business_id
            or link.supplier_business_id != business_id
            or movement.source_document_id != link.receipt_id
            or movement.source_line_id != link.receipt_item_id
            or link.receipt_purchase_order_id != link.purchase_order_id
            or link.purchase_order_item_purchase_order_id != link.purchase_order_id
            or link.purchase_order_item_ingredient_id != movement.ingredient_id
        ):
            raise GoodsReceiptTraceUnavailable(
                "The linked receipt, purchase order, supplier, and stock references are inconsistent."
            )
