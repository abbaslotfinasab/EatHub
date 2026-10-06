from dataclasses import dataclass
from datetime import datetime

from purchase.domain.entities.purchase_invoice import PurchaseInvoice
from purchase.domain.enums.purchase_invoice_matching_status import PurchaseInvoiceMatchingStatus
from purchase.domain.services.purchase_invoice_matcher import (
    PurchaseInvoiceMatchLineInput,
    PurchaseInvoiceMatchResult,
)


@dataclass(frozen=True)
class PurchaseInvoiceMatchingContext:
    invoice: PurchaseInvoice
    lines: tuple[PurchaseInvoiceMatchLineInput, ...]
    matching_status: PurchaseInvoiceMatchingStatus
    matched_at: datetime | None


@dataclass(frozen=True)
class LastPersistedPurchaseInvoiceMatch:
    status: PurchaseInvoiceMatchingStatus
    matched_at: datetime | None


@dataclass(frozen=True)
class PurchaseInvoiceMatchResponse:
    current: PurchaseInvoiceMatchResult
    last_persisted: LastPersistedPurchaseInvoiceMatch
