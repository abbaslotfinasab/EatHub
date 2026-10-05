from purchase.application.dto.purchase_invoice import ApprovePurchaseInvoiceDTO
from purchase.application.ports.goods_receipt import TransactionManager
from purchase.domain.repositories.purchase_invoice_repository import (
    PurchaseInvoiceRepository,
)


class ApprovePurchaseInvoiceUseCase:
    def __init__(
        self,
        repository: PurchaseInvoiceRepository,
        transaction_manager: TransactionManager,
    ) -> None:
        self._repository = repository
        self._transaction_manager = transaction_manager

    def execute(self, command: ApprovePurchaseInvoiceDTO):
        self._validate_positive_id(command.business_id, "Business ID")
        self._validate_positive_id(
            command.purchase_invoice_id,
            "Purchase invoice ID",
        )
        self._validate_positive_id(command.approved_by_id, "Approval actor ID")

        with self._transaction_manager.atomic():
            invoice = self._repository.get_by_id_for_business(
                command.purchase_invoice_id,
                command.business_id,
            )
            if invoice is None:
                raise ValueError("Purchase invoice does not exist in this business.")
            invoice.approve(command.approved_by_id, command.approved_at)
            return self._repository.save(invoice)

    @staticmethod
    def _validate_positive_id(value: int, field_name: str) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")
