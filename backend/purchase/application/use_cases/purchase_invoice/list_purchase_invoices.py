from purchase.application.dto.purchase_invoice import ListPurchaseInvoicesQuery
from purchase.domain.entities.purchase_invoice import PurchaseInvoice
from purchase.domain.repositories.purchase_invoice_repository import PurchaseInvoiceRepository


class ListPurchaseInvoicesUseCase:
    def __init__(self, repository: PurchaseInvoiceRepository) -> None:
        self._repository = repository

    def execute(self, query: ListPurchaseInvoicesQuery) -> list[PurchaseInvoice]:
        return self._repository.list(
            query.business_id,
            supplier_id=query.supplier_id,
            purchase_order_id=query.purchase_order_id,
            invoice_date_from=query.invoice_date_from,
            invoice_date_to=query.invoice_date_to,
        )
