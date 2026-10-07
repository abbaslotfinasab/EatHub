from datetime import datetime
from decimal import Decimal

from django.db.models import Prefetch, Sum

from purchase.application.dto.purchase_invoice_matching import PurchaseInvoiceMatchingContext
from purchase.application.ports.purchase_invoice_matching import PurchaseInvoiceMatchingRepository
from purchase.domain.enums.purchase_invoice_matching_status import PurchaseInvoiceMatchingStatus
from purchase.domain.enums.purchase_invoice_status import PurchaseInvoiceStatus
from purchase.domain.services.purchase_invoice_matcher import PurchaseInvoiceMatchLineInput
from purchase.infrastructure.persistence.django.mappers import PurchaseInvoiceMapper
from purchase.models import (
    GoodsReceiptItem as DjangoGoodsReceiptItem,
    PurchaseInvoice as DjangoPurchaseInvoice,
    PurchaseInvoiceItem as DjangoPurchaseInvoiceItem,
    PurchaseOrderItem as DjangoPurchaseOrderItem,
)


class DjangoPurchaseInvoiceMatchingRepository(PurchaseInvoiceMatchingRepository):
    def lock_invoice_for_matching(self, business_id: int, invoice_id: int) -> bool:
        # Lock only the invoice row: joining nullable purchase_order here can
        # produce an invalid PostgreSQL FOR UPDATE outer-join clause.
        return DjangoPurchaseInvoice.objects.select_for_update(of=("self",)).filter(
            id=invoice_id, business_id=business_id,
        ).exists()

    def load_matching_context(
        self, business_id: int, invoice_id: int
    ) -> PurchaseInvoiceMatchingContext | None:
        item_queryset = DjangoPurchaseInvoiceItem.objects.select_related(
            "purchase_order_item", "purchase_order_item__ingredient",
        ).order_by("id")
        queryset = DjangoPurchaseInvoice.objects.select_related(
            "business", "supplier", "purchase_order",
        ).prefetch_related(Prefetch("items", queryset=item_queryset))
        invoice_model = queryset.filter(
            id=invoice_id, business_id=business_id,
        ).first()
        if invoice_model is None:
            return None

        invoice_items = list(invoice_model.items.all())
        po_item_ids = {item.purchase_order_item_id for item in invoice_items}
        po_items = {
            item.id: item
            for item in DjangoPurchaseOrderItem.objects.select_related("ingredient").filter(
                id__in=po_item_ids,
                purchase_order_id=invoice_model.purchase_order_id,
                purchase_order__business_id=business_id,
                ingredient__business_id=business_id,
            )
        }
        if set(po_items) != po_item_ids:
            raise ValueError("Invoice item references a purchase order item outside its purchase order or business.")

        accepted_rows = DjangoGoodsReceiptItem.objects.filter(
            receipt__business_id=business_id,
            receipt__purchase_order_id=invoice_model.purchase_order_id,
            purchase_order_item_id__in=po_item_ids,
        ).values("purchase_order_item_id").annotate(
            quantity=Sum("received_quantity"),
        )
        accepted = {
            row["purchase_order_item_id"]: row["quantity"] or Decimal("0")
            for row in accepted_rows
        }

        # Approved and posted invoices both consume received quantity.
        previous_rows = DjangoPurchaseInvoiceItem.objects.filter(
            purchase_invoice__business_id=business_id,
            purchase_invoice__purchase_order_id=invoice_model.purchase_order_id,
            purchase_invoice__status__in=(
                DjangoPurchaseInvoice.Status.APPROVED,
                DjangoPurchaseInvoice.Status.POSTED,
            ),
            purchase_order_item_id__in=po_item_ids,
        ).exclude(purchase_invoice_id=invoice_id).values(
            "purchase_order_item_id",
        ).annotate(quantity=Sum("quantity"))
        previous = {
            row["purchase_order_item_id"]: row["quantity"] or Decimal("0")
            for row in previous_rows
        }

        lines = tuple(
            PurchaseInvoiceMatchLineInput(
                invoice_item_id=item.id,
                purchase_order_item_id=item.purchase_order_item_id,
                ordered_quantity=po_items[item.purchase_order_item_id].quantity,
                accepted_received_quantity=accepted.get(item.purchase_order_item_id, Decimal("0")),
                previously_invoiced_quantity=previous.get(item.purchase_order_item_id, Decimal("0")),
                current_invoice_quantity=item.quantity,
                purchase_order_unit_price=po_items[item.purchase_order_item_id].unit_price,
                invoice_unit_price=item.unit_price,
            )
            for item in invoice_items
        )
        return PurchaseInvoiceMatchingContext(
            invoice=PurchaseInvoiceMapper.to_domain(invoice_model),
            lines=lines,
            matching_status=PurchaseInvoiceMatchingStatus(invoice_model.matching_status),
            matched_at=invoice_model.matched_at,
        )

    def save_matching_state(
        self, business_id: int, invoice_id: int,
        status: PurchaseInvoiceMatchingStatus, matched_at: datetime,
    ) -> None:
        updated = DjangoPurchaseInvoice.objects.filter(
            id=invoice_id, business_id=business_id,
            status=PurchaseInvoiceStatus.APPROVED.value,
        ).update(matching_status=status.value, matched_at=matched_at)
        if updated != 1:
            raise ValueError("Only approved purchase invoices can persist matching state.")
