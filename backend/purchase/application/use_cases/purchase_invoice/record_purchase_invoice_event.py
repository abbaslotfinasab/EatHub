from typing import Protocol

from purchase.application.dto.purchase_invoice_event import RecordPurchaseInvoiceEventDTO


class PurchaseInvoiceEventWriteRepository(Protocol):
    def create(self, data: RecordPurchaseInvoiceEventDTO) -> None:
        ...


class RecordPurchaseInvoiceEventUseCase:
    def __init__(self, repository: PurchaseInvoiceEventWriteRepository) -> None:
        self._repository = repository

    def execute(self, data: RecordPurchaseInvoiceEventDTO) -> None:
        self._repository.create(data)
