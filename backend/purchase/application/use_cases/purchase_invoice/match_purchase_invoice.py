from datetime import datetime, timezone

from purchase.application.dto.purchase_invoice_matching import (
    LastPersistedPurchaseInvoiceMatch,
    PurchaseInvoiceMatchResponse,
)
from purchase.application.ports.goods_receipt import TransactionManager
from purchase.application.ports.purchase_invoice_matching import PurchaseInvoiceMatchingRepository
from purchase.domain.enums.purchase_invoice_status import PurchaseInvoiceStatus
from purchase.domain.services.purchase_invoice_matcher import PurchaseInvoiceMatcher


class MatchPurchaseInvoiceUseCase:
    def __init__(
        self,
        repository: PurchaseInvoiceMatchingRepository,
        transaction_manager: TransactionManager,
        matcher: PurchaseInvoiceMatcher | None = None,
        clock=None,
    ) -> None:
        self._repository = repository
        self._transaction_manager = transaction_manager
        self._matcher = matcher or PurchaseInvoiceMatcher()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def execute(
        self, business_id: int, invoice_id: int, *, persist: bool = True
    ) -> PurchaseInvoiceMatchResponse:
        self._validate_id(business_id, "Business ID")
        self._validate_id(invoice_id, "Purchase invoice ID")
        with self._transaction_manager.atomic():
            if persist and not self._repository.lock_invoice_for_matching(business_id, invoice_id):
                raise ValueError("Purchase invoice does not exist in this business.")
            context = self._repository.load_matching_context(business_id, invoice_id)
            if context is None:
                raise ValueError("Purchase invoice does not exist in this business.")
            if context.invoice.status not in (
                PurchaseInvoiceStatus.APPROVED,
                PurchaseInvoiceStatus.POSTED,
            ):
                raise ValueError("Only approved or posted purchase invoices can be matched.")
            result = self._matcher.match(context.invoice, list(context.lines))
            matched_at = self._clock() if persist else context.matched_at
            if persist:
                self._repository.save_matching_state(
                    business_id, invoice_id, result.status, matched_at,
                )
            return PurchaseInvoiceMatchResponse(
                current=result,
                last_persisted=LastPersistedPurchaseInvoiceMatch(
                    status=result.status if persist else context.matching_status,
                    matched_at=matched_at,
                ),
            )

    @staticmethod
    def _validate_id(value: int, name: str) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} must be a positive integer.")
