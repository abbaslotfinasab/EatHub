"""Composition root for Purchase application use cases.

This outer-layer module wires application use cases to Django infrastructure
adapters. Presentation modules should depend on these factories rather than
constructing infrastructure adapters directly.
"""

from purchase.application.use_cases.payment_allocation.create_payment_allocation import (
    CreatePaymentAllocation,
)
from purchase.application.use_cases.payment_allocation.get_payment_allocation import (
    GetPaymentAllocation,
)
from purchase.application.use_cases.payment_allocation.list_payment_allocations import (
    ListPaymentAllocations,
)
from purchase.application.use_cases.accounts_payable.get_accounts_payable import (
    GetAccountsPayableUseCase,
)
from purchase.application.use_cases.accounts_payable.get_accounts_payable_payment_eligibility import (
    GetAccountsPayablePaymentEligibility,
)
from purchase.application.use_cases.accounts_payable.list_accounts_payables import (
    ListAccountsPayablesUseCase,
)
from purchase.application.use_cases.supplier_payment.create_supplier_payment import (
    CreateSupplierPaymentUseCase,
)
from purchase.application.use_cases.supplier_payment.get_supplier_payment import (
    GetSupplierPaymentUseCase,
)
from purchase.application.use_cases.supplier_payment.list_supplier_payments import (
    ListSupplierPaymentsUseCase,
)
from purchase.application.use_cases.supplier_payment.list_supplier_payment_allocation_totals import (
    ListSupplierPaymentAllocationTotalsUseCase,
)
from purchase.application.use_cases.purchase_invoice.cancel_purchase_invoice import (
    CancelPurchaseInvoice,
)
from purchase.application.use_cases.purchase_invoice.list_purchase_invoice_events import (
    ListPurchaseInvoiceEventsUseCase,
)
from purchase.application.use_cases.purchase_invoice.match_purchase_invoice import (
    MatchPurchaseInvoiceUseCase,
)
from purchase.application.use_cases.purchase_invoice.post_purchase_invoice import (
    PostPurchaseInvoice,
)
from purchase.application.use_cases.purchase_invoice.record_purchase_invoice_event import (
    RecordPurchaseInvoiceEventUseCase,
)
from purchase.infrastructure.persistence.django.repositories.accounts_payable_repository import (
    DjangoAccountsPayableRepository,
)
from purchase.infrastructure.persistence.django.repositories.payment_allocation_repository import (
    DjangoPaymentAllocationRepository,
)
from purchase.infrastructure.persistence.django.repositories.supplier_payment_repository import (
    DjangoSupplierPaymentRepository,
)
from purchase.infrastructure.persistence.django.repositories.supplier_repository import (
    DjangoSupplierRepository,
)
from purchase.infrastructure.persistence.django.repositories.purchase_invoice_event_read_repository import (
    DjangoPurchaseInvoiceEventReadRepository,
)
from purchase.infrastructure.persistence.django.repositories.purchase_invoice_event_write_repository import (
    DjangoPurchaseInvoiceEventWriteRepository,
)
from purchase.infrastructure.persistence.django.repositories.purchase_invoice_matching_repository import (
    DjangoPurchaseInvoiceMatchingRepository,
)
from purchase.infrastructure.persistence.django.repositories.purchase_invoice_repository import (
    DjangoPurchaseInvoiceRepository,
)
from purchase.infrastructure.persistence.transaction import (
    DjangoTransactionManager,
)


def purchase_invoice_repository():
    return DjangoPurchaseInvoiceRepository()


def purchase_invoice_transaction_manager():
    return DjangoTransactionManager()


def purchase_invoice_matching_use_case():
    return MatchPurchaseInvoiceUseCase(
        DjangoPurchaseInvoiceMatchingRepository(),
        purchase_invoice_transaction_manager(),
    )


def purchase_invoice_posting_use_case():
    transaction_manager = purchase_invoice_transaction_manager()
    return PostPurchaseInvoice(
        purchase_invoice_repository(),
        DjangoAccountsPayableRepository(),
        MatchPurchaseInvoiceUseCase(
            DjangoPurchaseInvoiceMatchingRepository(),
            transaction_manager,
        ),
        transaction_manager,
    )


def purchase_invoice_cancel_use_case():
    return CancelPurchaseInvoice(
        purchase_invoice_repository(),
        DjangoAccountsPayableRepository(),
        purchase_invoice_transaction_manager(),
    )


def purchase_invoice_event_write_use_case():
    return RecordPurchaseInvoiceEventUseCase(
        DjangoPurchaseInvoiceEventWriteRepository()
    )


def purchase_invoice_event_read_use_case():
    return ListPurchaseInvoiceEventsUseCase(
        DjangoPurchaseInvoiceEventReadRepository()
    )


def accounts_payable_repository():
    return DjangoAccountsPayableRepository()


def list_accounts_payables_use_case():
    return ListAccountsPayablesUseCase(accounts_payable_repository())


def get_accounts_payable_use_case():
    return GetAccountsPayableUseCase(accounts_payable_repository())


def accounts_payable_payment_eligibility_use_case():
    return GetAccountsPayablePaymentEligibility(
        accounts_payable_repository(),
        DjangoPaymentAllocationRepository(),
    )


def payment_allocation_repository():
    return DjangoPaymentAllocationRepository()


def create_payment_allocation_use_case():
    return CreatePaymentAllocation(
        accounts_payable_repository(),
        DjangoSupplierPaymentRepository(),
        payment_allocation_repository(),
        DjangoTransactionManager(),
    )


def list_payment_allocations_use_case():
    return ListPaymentAllocations(payment_allocation_repository())


def get_payment_allocation_use_case():
    return GetPaymentAllocation(payment_allocation_repository())


def supplier_payment_repository():
    return DjangoSupplierPaymentRepository()


def create_supplier_payment_use_case():
    return CreateSupplierPaymentUseCase(
        supplier_payment_repository(),
        DjangoSupplierRepository(),
    )


def list_supplier_payments_use_case():
    return ListSupplierPaymentsUseCase(supplier_payment_repository())


def get_supplier_payment_use_case():
    return GetSupplierPaymentUseCase(supplier_payment_repository())


def list_supplier_payment_allocation_totals_use_case():
    return ListSupplierPaymentAllocationTotalsUseCase(
        payment_allocation_repository()
    )
