from purchase.application.dto.accounts_payable import CreateAccountsPayableDTO
from purchase.application.ports.goods_receipt import TransactionManager
from purchase.application.use_cases.purchase_invoice.match_purchase_invoice import (
    MatchPurchaseInvoiceUseCase,
)
from purchase.domain.entities.accounts_payable import AccountsPayable
from purchase.domain.enums.accounts_payable_status import AccountsPayableStatus
from purchase.domain.enums.purchase_invoice_matching_status import PurchaseInvoiceMatchingStatus
from purchase.domain.enums.purchase_invoice_status import PurchaseInvoiceStatus
from purchase.domain.repositories.accounts_payable_repository import AccountsPayableRepository
from purchase.domain.repositories.purchase_invoice_repository import PurchaseInvoiceRepository
from purchase.domain.repositories.supplier_repository import SupplierRepository


class CreateAccountsPayableUseCase:
    def __init__(
        self,
        accounts_payable_repository: AccountsPayableRepository,
        purchase_invoice_repository: PurchaseInvoiceRepository,
        supplier_repository: SupplierRepository,
        match_purchase_invoice: MatchPurchaseInvoiceUseCase,
        transaction_manager: TransactionManager,
    ) -> None:
        self._accounts_payable_repository = accounts_payable_repository
        self._purchase_invoice_repository = purchase_invoice_repository
        self._supplier_repository = supplier_repository
        self._match_purchase_invoice = match_purchase_invoice
        self._transaction_manager = transaction_manager

    def execute(self, command: CreateAccountsPayableDTO) -> AccountsPayable:
        business_id = self._positive_id(command.business_id, "Business ID")
        invoice_id = self._positive_id(command.source_invoice_id, "Source invoice ID")

        with self._transaction_manager.atomic():
            if not self._accounts_payable_repository.lock_source_invoice_for_creation(
                business_id, invoice_id,
            ):
                raise ValueError("Purchase invoice does not exist in this business.")

            invoice = self._purchase_invoice_repository.get_by_id_for_business(
                invoice_id, business_id,
            )
            if invoice is None:
                raise ValueError("Purchase invoice does not exist in this business.")
            if invoice.status != PurchaseInvoiceStatus.APPROVED:
                raise ValueError("Only approved purchase invoices can create accounts payable.")
            if self._accounts_payable_repository.exists_for_source_invoice(invoice_id, business_id):
                raise ValueError("Accounts payable already exists for this purchase invoice.")

            supplier = self._supplier_repository.get_by_id_for_business(
                invoice.supplier_id, business_id,
            )
            if supplier is None:
                raise ValueError("Purchase invoice supplier does not exist in this business.")

            current_match = self._match_purchase_invoice.execute(
                business_id, invoice_id, persist=False,
            )
            if current_match.current.status != PurchaseInvoiceMatchingStatus.MATCHED:
                raise ValueError("Purchase invoice must have a current MATCHED result to create accounts payable.")

            payable = AccountsPayable(
                id=None,
                business_id=business_id,
                supplier_id=invoice.supplier_id,
                source_invoice_id=invoice.id,
                amount=invoice.total_price,
                due_date=command.due_date,
                status=AccountsPayableStatus.OPEN,
            )
            return self._accounts_payable_repository.create(payable)

    @staticmethod
    def _positive_id(value: int, label: str) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{label} must be a positive integer.")
        return value
