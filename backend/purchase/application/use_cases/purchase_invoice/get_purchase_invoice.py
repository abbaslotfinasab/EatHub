from purchase.domain.entities.purchase_invoice import PurchaseInvoice
from purchase.domain.repositories.purchase_invoice_repository import PurchaseInvoiceRepository


class GetPurchaseInvoiceUseCase:
    def __init__(self, repository: PurchaseInvoiceRepository) -> None:
        self._repository = repository

    def execute(self, purchase_invoice_id: int, business_id: int) -> PurchaseInvoice:
        invoice = self._repository.get_by_id_for_business(purchase_invoice_id, business_id)
        if invoice is None:
            raise ValueError("Purchase invoice does not exist in this business.")
        return invoice
