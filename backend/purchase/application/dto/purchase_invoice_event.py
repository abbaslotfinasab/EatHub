from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RecordPurchaseInvoiceEventDTO:
    business_id: int
    purchase_invoice_id: int
    actor_id: int | None
    event_type: str
    previous_status: str | None
    resulting_status: str | None
    metadata: dict[str, Any]
