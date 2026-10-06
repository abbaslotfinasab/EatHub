from abc import ABC, abstractmethod
from datetime import datetime

from purchase.application.dto.purchase_invoice_matching import PurchaseInvoiceMatchingContext
from purchase.domain.enums.purchase_invoice_matching_status import PurchaseInvoiceMatchingStatus


class PurchaseInvoiceMatchingRepository(ABC):
    @abstractmethod
    def lock_invoice_for_matching(self, business_id: int, invoice_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def load_matching_context(
        self, business_id: int, invoice_id: int
    ) -> PurchaseInvoiceMatchingContext | None:
        raise NotImplementedError

    @abstractmethod
    def save_matching_state(
        self, business_id: int, invoice_id: int,
        status: PurchaseInvoiceMatchingStatus, matched_at: datetime,
    ) -> None:
        raise NotImplementedError
