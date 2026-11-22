from typing import Protocol

from purchase.application.dto.purchase_invoice_event import PurchaseInvoiceEventReadDTO


class PurchaseInvoiceEventReadRepository(Protocol):
    def list_for_invoice(
        self,
        *,
        business_id: int,
        purchase_invoice_id: int,
    ) -> list[PurchaseInvoiceEventReadDTO]:
        ...


class ListPurchaseInvoiceEventsUseCase:
    def __init__(self, repository: PurchaseInvoiceEventReadRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        business_id: int,
        purchase_invoice_id: int,
    ) -> list[PurchaseInvoiceEventReadDTO]:
        return self._repository.list_for_invoice(
            business_id=business_id,
            purchase_invoice_id=purchase_invoice_id,
        )
