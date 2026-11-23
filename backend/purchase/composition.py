"""Composition root for Purchase Invoice application use cases.

This outer-layer module is the only place where Purchase Invoice use cases
are wired to Django infrastructure adapters.
"""

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
