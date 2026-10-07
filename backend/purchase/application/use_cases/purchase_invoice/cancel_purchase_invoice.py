from purchase.application.dto.purchase_invoice import CancelPurchaseInvoiceDTO
from purchase.application.ports.goods_receipt import TransactionManager
from purchase.domain.enums.purchase_invoice_status import PurchaseInvoiceStatus
from purchase.domain.repositories.accounts_payable_repository import AccountsPayableRepository
from purchase.domain.repositories.purchase_invoice_repository import PurchaseInvoiceRepository


class CancelPurchaseInvoice:
    def __init__(self, invoice_repository: PurchaseInvoiceRepository,
                 accounts_payable_repository: AccountsPayableRepository,
                 transaction_manager: TransactionManager) -> None:
        self._invoice_repository = invoice_repository
        self._accounts_payable_repository = accounts_payable_repository
        self._transaction_manager = transaction_manager

    def execute(self, command: CancelPurchaseInvoiceDTO):
        for value, label in (
            (command.business_id, "Business ID"),
            (command.purchase_invoice_id, "Purchase invoice ID"),
            (command.cancelled_by_id, "Cancellation actor ID"),
        ):
            if not isinstance(value, int) or value <= 0:
                raise ValueError(f"{label} must be a positive integer.")
        if not isinstance(command.reason, str) or not command.reason.strip():
            raise ValueError("Cancellation reason is required.")

        with self._transaction_manager.atomic():
            if not self._invoice_repository.lock_for_cancellation(
                command.business_id, command.purchase_invoice_id,
            ):
                raise ValueError("Purchase invoice does not exist in this business.")
            invoice = self._invoice_repository.get_by_id_for_business(
                command.purchase_invoice_id, command.business_id,
            )
            if invoice is None:
                raise ValueError("Purchase invoice does not exist in this business.")
            if invoice.status not in (PurchaseInvoiceStatus.DRAFT, PurchaseInvoiceStatus.APPROVED):
                raise ValueError(f"Purchase invoice cannot be cancelled from status '{invoice.status}'.")
            if self._accounts_payable_repository.exists_for_source_invoice(
                invoice.id, command.business_id,
            ):
                raise ValueError("Purchase invoice with an accounts payable cannot be cancelled.")
            invoice.cancel(command.cancelled_by_id, command.cancelled_at, command.reason)
            return self._invoice_repository.save_cancelled(invoice)
