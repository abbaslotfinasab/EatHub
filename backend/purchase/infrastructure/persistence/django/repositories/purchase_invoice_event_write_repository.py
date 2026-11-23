from purchase.application.dto.purchase_invoice_event import PurchaseInvoiceEventWriteDTO
from purchase.models import PurchaseInvoiceEvent


class DjangoPurchaseInvoiceEventWriteRepository:
    """Django adapter for appending immutable purchase invoice audit events."""

    def create(self, event: PurchaseInvoiceEventWriteDTO) -> int:
        row = PurchaseInvoiceEvent.objects.create(
            business_id=event.business_id,
            purchase_invoice_id=event.purchase_invoice_id,
            actor_id=event.actor_id,
            event_type=event.event_type,
            previous_status=event.previous_status,
            resulting_status=event.resulting_status,
            metadata=event.metadata,
        )
        return row.id
