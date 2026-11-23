from typing import Protocol

from purchase.application.dto.purchase_invoice_event import PurchaseInvoiceEventWriteDTO


class PurchaseInvoiceEventWriteRepository(Protocol):
    def create(self, event: PurchaseInvoiceEventWriteDTO) -> int:
        ...


class RecordPurchaseInvoiceEventUseCase:
    def __init__(self, repository: PurchaseInvoiceEventWriteRepository) -> None:
        self._repository = repository

    def execute(self, event: PurchaseInvoiceEventWriteDTO) -> int:
        return self._repository.create(event)
