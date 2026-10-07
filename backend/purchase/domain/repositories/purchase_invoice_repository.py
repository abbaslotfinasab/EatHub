from abc import ABC, abstractmethod
from datetime import date

from purchase.domain.entities.purchase_invoice import PurchaseInvoice


class PurchaseInvoiceRepository(ABC):

    @abstractmethod
    def get_by_id_for_business(
        self,
        purchase_invoice_id: int,
        business_id: int,
    ) -> PurchaseInvoice | None:
        """Return a purchase invoice, including its items, within a business."""
        raise NotImplementedError

    @abstractmethod
    def lock_for_posting(self, business_id: int, purchase_invoice_id: int) -> bool:
        """Lock only the tenant-scoped invoice row for a posting command."""
        raise NotImplementedError

    @abstractmethod
    def save_posted(self, purchase_invoice: PurchaseInvoice) -> PurchaseInvoice:
        """Persist the APPROVED -> POSTED lifecycle transition."""
        raise NotImplementedError

    @abstractmethod
    def save_approved(self, purchase_invoice: PurchaseInvoice) -> PurchaseInvoice:
        """Persist the DRAFT -> APPROVED lifecycle transition."""
        raise NotImplementedError

    @abstractmethod
    def lock_for_cancellation(self, business_id: int, purchase_invoice_id: int) -> bool:
        """Lock only the tenant-scoped invoice row for cancellation."""
        raise NotImplementedError

    @abstractmethod
    def save_cancelled(self, purchase_invoice: PurchaseInvoice) -> PurchaseInvoice:
        """Persist the DRAFT/APPROVED -> CANCELLED transition only."""
        raise NotImplementedError

    @abstractmethod
    def list(
        self,
        business_id: int,
        *,
        supplier_id: int | None = None,
        purchase_order_id: int | None = None,
        invoice_date_from: date | None = None,
        invoice_date_to: date | None = None,
    ) -> list[PurchaseInvoice]:
        """Return purchase invoices belonging to a business."""
        raise NotImplementedError

    @abstractmethod
    def exists_by_number(
        self,
        business_id: int,
        supplier_id: int,
        invoice_number: str,
        *,
        exclude_id: int | None = None,
    ) -> bool:
        """Check whether an invoice number exists for a supplier in a business."""
        raise NotImplementedError

    @abstractmethod
    def save(
        self,
        purchase_invoice: PurchaseInvoice,
    ) -> PurchaseInvoice:
        """Create or update a purchase invoice together with its items."""
        raise NotImplementedError
