from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class PurchaseInvoiceEventReadDTO:
    id: int
    event_type: str
    actor_id: int | None
    actor_name: str | None
    previous_status: str | None
    resulting_status: str | None
    metadata: dict[str, Any]
    occurred_at: datetime


@dataclass(frozen=True)
class RecordPurchaseInvoiceEventDTO:
    business_id: int
    purchase_invoice_id: int
    actor_id: int | None
    event_type: str
    previous_status: str | None
    resulting_status: str | None
    metadata: dict[str, Any]
