from dataclasses import dataclass
from datetime import date, datetime

from purchase.domain.entities.accounts_payable import AccountsPayable
from purchase.domain.entities.purchase_invoice import PurchaseInvoice


@dataclass(frozen=True)
class PostPurchaseInvoiceDTO:
    business_id: int
    purchase_invoice_id: int
    posted_by_id: int
    posted_at: datetime
    due_date: date | None = None


@dataclass(frozen=True)
class PostPurchaseInvoiceResult:
    invoice: PurchaseInvoice
    accounts_payable: AccountsPayable
