from purchase.domain.entities.supplier import Supplier
from purchase.domain.entities.requisition import (
    PurchaseRequisition,
    PurchaseRequisitionItem,
)
from purchase.domain.entities.purchase_order import (
    PurchaseOrder,
    PurchaseOrderItem,
)
from purchase.domain.entities.goods_receipt import (
    GoodsReceipt,
    GoodsReceiptItem,
)
from purchase.domain.enums.requisition_status import RequisitionStatus
from purchase.domain.enums.purchase_order_status import PurchaseOrderStatus
from purchase.models import (
    PurchaseRequisition as DjangoPurchaseRequisition,
    PurchaseRequisitionItem as DjangoPurchaseRequisitionItem,
    PurchaseOrder as DjangoPurchaseOrder,
    PurchaseOrderItem as DjangoPurchaseOrderItem,
    Supplier as DjangoSupplier,
    GoodsReceipt as DjangoGoodsReceipt,
    GoodsReceiptItem as DjangoGoodsReceiptItem,
)


class SupplierMapper:
    @staticmethod
    def to_domain(model: DjangoSupplier) -> Supplier:
        return Supplier(
            id=model.id,
            business_id=model.business_id,
            name=model.name,
            phone=model.phone,
            email=model.email,
            address=model.address,
            tax_number=model.tax_number,
            is_active=model.is_active,
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: Supplier,
        model: DjangoSupplier | None = None,
    ) -> DjangoSupplier:
        if model is None:
            model = DjangoSupplier()

        model.business_id = entity.business_id
        model.name = entity.name
        model.phone = entity.phone
        model.email = entity.email
        model.address = entity.address
        model.tax_number = entity.tax_number
        model.is_active = entity.is_active
        model.notes = entity.notes

        return model


class PurchaseRequisitionMapper:
    @staticmethod
    def to_domain(
        model: DjangoPurchaseRequisition,
    ) -> PurchaseRequisition:
        return PurchaseRequisition(
            id=model.id,
            business_id=model.business_id,
            requested_by_id=model.requested_by_id,
            status=RequisitionStatus(model.status),
            reason=model.reason,
            items=[
                PurchaseRequisitionItem(
                    ingredient_id=item.ingredient_id,
                    quantity=item.quantity,
                    note=item.note,
                )
                for item in model.items.all()
            ],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: PurchaseRequisition,
        model: DjangoPurchaseRequisition | None = None,
    ) -> DjangoPurchaseRequisition:
        if model is None:
            model = DjangoPurchaseRequisition()

        model.id = entity.id
        model.business_id = entity.business_id
        model.requested_by_id = entity.requested_by_id
        model.status = entity.status
        model.reason = entity.reason
        model.created_at = entity.created_at
        model.updated_at = entity.updated_at

        return model

    @staticmethod
    def item_to_model(
        item: PurchaseRequisitionItem,
        requisition: DjangoPurchaseRequisition,
    ) -> DjangoPurchaseRequisitionItem:
        return DjangoPurchaseRequisitionItem(
            requisition=requisition,
            ingredient_id=item.ingredient_id,
            quantity=item.quantity,
            note=item.note,
        )


class PurchaseOrderMapper:
    @staticmethod
    def to_domain(model: DjangoPurchaseOrder) -> PurchaseOrder:
        return PurchaseOrder(
            id=model.id,
            business_id=model.business_id,
            supplier_id=model.supplier_id,
            requisition_id=model.requisition_id,
            status=PurchaseOrderStatus(model.status),
            order_date=model.order_date,
            expected_date=model.expected_date,
            discount=model.discount,
            tax=model.tax,
            items=[
                PurchaseOrderItem(
                    ingredient_id=item.ingredient_id,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                )
                for item in model.items.all()
            ],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: PurchaseOrder,
        model: DjangoPurchaseOrder | None = None,
    ) -> DjangoPurchaseOrder:
        if model is None:
            model = DjangoPurchaseOrder()

        model.id = entity.id
        model.business_id = entity.business_id
        model.supplier_id = entity.supplier_id
        model.requisition_id = entity.requisition_id
        model.status = entity.status
        model.order_date = entity.order_date
        model.expected_date = entity.expected_date
        model.subtotal = entity.subtotal
        model.discount = entity.discount
        model.tax = entity.tax
        model.total = entity.total
        model.created_at = entity.created_at
        model.updated_at = entity.updated_at

        return model

    @staticmethod
    def item_to_model(
        item: PurchaseOrderItem,
        purchase_order: DjangoPurchaseOrder,
    ) -> DjangoPurchaseOrderItem:
        return DjangoPurchaseOrderItem(
            purchase_order=purchase_order,
            ingredient_id=item.ingredient_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
        )


class GoodsReceiptMapper:
    @staticmethod
    def to_domain(model: DjangoGoodsReceipt) -> GoodsReceipt:
        return GoodsReceipt(
            id=model.id,
            business_id=model.business_id,
            purchase_order_id=model.purchase_order_id,
            received_by_id=model.received_by_id,
            received_date=model.received_date,
            notes=model.notes,
            items=[
                GoodsReceiptItem(
                    purchase_order_item_id=item.purchase_order_item_id,
                    received_quantity=item.received_quantity,
                    rejected_quantity=item.rejected_quantity,
                )
                for item in model.items.all()
            ],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: GoodsReceipt,
        model: DjangoGoodsReceipt | None = None,
    ) -> DjangoGoodsReceipt:
        if model is None:
            model = DjangoGoodsReceipt()

        model.id = entity.id
        model.business_id = entity.business_id
        model.purchase_order_id = entity.purchase_order_id
        model.received_by_id = entity.received_by_id
        model.received_date = entity.received_date
        model.notes = entity.notes
        model.created_at = entity.created_at
        model.updated_at = entity.updated_at

        return model

    @staticmethod
    def item_to_model(
        item: GoodsReceiptItem,
        receipt: DjangoGoodsReceipt,
    ) -> DjangoGoodsReceiptItem:
        return DjangoGoodsReceiptItem(
            receipt=receipt,
            purchase_order_item_id=item.purchase_order_item_id,
            received_quantity=item.received_quantity,
            rejected_quantity=item.rejected_quantity,
        )
