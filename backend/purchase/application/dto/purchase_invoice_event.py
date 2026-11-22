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
    resulting_status: str
    metadata: dict[str, Any]
    occurred_at: datetime
