from purchase.application.dto.purchase_invoice_posting import (
    PostPurchaseInvoiceDTO,
    PostPurchaseInvoiceResult,
)
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


class PostPurchaseInvoice:
    def __init__(
        self,
        invoice_repository: PurchaseInvoiceRepository,
        accounts_payable_repository: AccountsPayableRepository,
        matcher: MatchPurchaseInvoiceUseCase,
        transaction_manager: TransactionManager,
    ) -> None:
        self._invoice_repository = invoice_repository
        self._accounts_payable_repository = accounts_payable_repository
        self._matcher = matcher
        self._transaction_manager = transaction_manager

    def execute(self, command: PostPurchaseInvoiceDTO) -> PostPurchaseInvoiceResult:
        self._positive_id(command.business_id, "Business ID")
        self._positive_id(command.purchase_invoice_id, "Purchase invoice ID")
        self._positive_id(command.posted_by_id, "Posting actor ID")

        with self._transaction_manager.atomic():
            if not self._invoice_repository.lock_for_posting(
                command.business_id, command.purchase_invoice_id,
            ):
                raise ValueError("Purchase invoice does not exist in this business.")

            invoice = self._invoice_repository.get_by_id_for_business(
                command.purchase_invoice_id,
                command.business_id,
            )
            if invoice is None:
                raise ValueError("Purchase invoice does not exist in this business.")
            if invoice.status != PurchaseInvoiceStatus.APPROVED:
                raise ValueError("Only approved purchase invoices can be posted.")

            current_match = self._matcher.execute(
                command.business_id,
                command.purchase_invoice_id,
                persist=True,
            )
            if current_match.current.status != PurchaseInvoiceMatchingStatus.MATCHED:
                raise ValueError("Purchase invoice requires a current MATCHED result to be posted.")
            invoice.matching_status = current_match.current.status
            invoice.matched_at = current_match.last_persisted.matched_at

            if self._accounts_payable_repository.exists_for_source_invoice(
                command.purchase_invoice_id,
                command.business_id,
            ):
                raise ValueError(
                    "Accounts payable already exists for this approved purchase invoice; posting state is inconsistent."
                )

            payable = self._accounts_payable_repository.create(AccountsPayable(
                id=None,
                business_id=invoice.business_id,
                supplier_id=invoice.supplier_id,
                source_invoice_id=invoice.id,
                amount=invoice.total_price,
                due_date=command.due_date,
                status=AccountsPayableStatus.OPEN,
            ))
            invoice.post(command.posted_by_id, command.posted_at)
            posted_invoice = self._invoice_repository.save_posted(invoice)
            return PostPurchaseInvoiceResult(
                invoice=posted_invoice,
                accounts_payable=payable,
            )

    @staticmethod
    def _positive_id(value: int, label: str) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{label} must be a positive integer.")
