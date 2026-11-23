from purchase.application.dto.purchase_invoice_event import RecordPurchaseInvoiceEventDTO
from purchase.models import PurchaseInvoice, PurchaseInvoiceEvent


class DjangoPurchaseInvoiceEventWriteRepository:
    """Django adapter for tenant-scoped purchase invoice audit event writes."""

    def create(self, data: RecordPurchaseInvoiceEventDTO) -> None:
        invoice_exists = PurchaseInvoice.objects.filter(
            id=data.purchase_invoice_id,
            business_id=data.business_id,
        ).exists()
        if not invoice_exists:
            raise ValueError("Purchase invoice does not exist in this business.")

        PurchaseInvoiceEvent.objects.create(
            business_id=data.business_id,
            purchase_invoice_id=data.purchase_invoice_id,
            actor_id=data.actor_id,
            event_type=data.event_type,
            previous_status=data.previous_status,
            resulting_status=data.resulting_status,
            metadata=data.metadata,
        )
