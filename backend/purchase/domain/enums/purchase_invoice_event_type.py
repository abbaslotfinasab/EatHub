from enum import StrEnum


class PurchaseInvoiceEventType(StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    APPROVED = "approved"
    MATCH_PERSISTED = "match_persisted"
    POSTED = "posted"
    CANCELLED = "cancelled"
