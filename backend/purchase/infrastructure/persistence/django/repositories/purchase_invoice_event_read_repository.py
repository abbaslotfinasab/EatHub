from purchase.application.dto.purchase_invoice_event import PurchaseInvoiceEventReadDTO
from purchase.models import PurchaseInvoiceEvent


class DjangoPurchaseInvoiceEventReadRepository:
    """Tenant-scoped Django adapter for immutable purchase invoice audit events."""

    def list_for_invoice(
        self,
        *,
        business_id: int,
        purchase_invoice_id: int,
    ) -> list[PurchaseInvoiceEventReadDTO]:
        rows = (
            PurchaseInvoiceEvent.objects.filter(
                business_id=business_id,
                purchase_invoice_id=purchase_invoice_id,
            )
            .select_related("actor")
            .order_by("occurred_at", "id")
        )
        return [
            PurchaseInvoiceEventReadDTO(
                id=row.id,
                event_type=row.event_type,
                actor_id=row.actor_id,
                actor_name=row.actor.name if row.actor_id else None,
                previous_status=row.previous_status,
                resulting_status=row.resulting_status,
                metadata=row.metadata,
                occurred_at=row.occurred_at,
            )
            for row in rows
        ]
