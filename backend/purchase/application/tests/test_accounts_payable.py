from contextlib import nullcontext
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase

from purchase.application.dto.accounts_payable import CreateAccountsPayableDTO
from purchase.application.use_cases.accounts_payable.create_accounts_payable import (
    CreateAccountsPayableUseCase,
)
from purchase.domain.entities.purchase_invoice import PurchaseInvoice, PurchaseInvoiceItem
from purchase.domain.enums.accounts_payable_status import AccountsPayableStatus
from purchase.domain.enums.purchase_invoice_matching_status import PurchaseInvoiceMatchingStatus
from purchase.domain.enums.purchase_invoice_status import PurchaseInvoiceStatus


class FakeTransactionManager:
    def atomic(self):
        return nullcontext()


class FakeAccountsPayableRepository:
    def __init__(self, *, exists=False, lock=True):
        self.exists = exists
        self.lock = lock
        self.created = None
        self.lock_calls = []

    def lock_source_invoice_for_creation(self, business_id, invoice_id):
        self.lock_calls.append((business_id, invoice_id))
        return self.lock

    def exists_for_source_invoice(self, invoice_id, business_id):
        return self.exists

    def create(self, payable):
        payable.id = 20
        self.created = payable
        return payable


class FakePurchaseInvoiceRepository:
    def __init__(self, invoice):
        self.invoice = invoice

    def get_by_id_for_business(self, invoice_id, business_id):
        if self.invoice.business_id != business_id or self.invoice.id != invoice_id:
            return None
        return self.invoice


class FakeSupplierRepository:
    def __init__(self, supplier_id=2):
        self.supplier_id = supplier_id

    def get_by_id_for_business(self, supplier_id, business_id):
        if supplier_id != self.supplier_id or business_id != 1:
            return None
        return SimpleNamespace(id=supplier_id, business_id=business_id)


class FakeMatchUseCase:
    def __init__(self, status=PurchaseInvoiceMatchingStatus.MATCHED):
        self.status = status
        self.calls = []

    def execute(self, business_id, invoice_id, *, persist):
        self.calls.append((business_id, invoice_id, persist))
        return SimpleNamespace(current=SimpleNamespace(status=self.status))


class CreateAccountsPayableUseCaseTests(SimpleTestCase):
    def invoice(self, status=PurchaseInvoiceStatus.APPROVED):
        approved = status == PurchaseInvoiceStatus.APPROVED
        return PurchaseInvoice(
            id=3,
            business_id=1,
            supplier_id=2,
            invoice_number="INV-3",
            invoice_date=date(2026, 10, 1),
            purchase_order_id=4,
            status=status,
            approved_by_id=7 if approved else None,
            approved_at=datetime(2026, 10, 1) if approved else None,
            items=[PurchaseInvoiceItem(
                ingredient_id=8,
                purchase_order_item_id=9,
                quantity=Decimal("2"),
                unit_price=Decimal("62.50"),
            )],
        )

    def use_case(self, invoice=None, *, matching_status=PurchaseInvoiceMatchingStatus.MATCHED,
                 exists=False, lock=True, supplier_id=2):
        ap_repository = FakeAccountsPayableRepository(exists=exists, lock=lock)
        matcher = FakeMatchUseCase(matching_status)
        use_case = CreateAccountsPayableUseCase(
            ap_repository,
            FakePurchaseInvoiceRepository(invoice or self.invoice()),
            FakeSupplierRepository(supplier_id),
            matcher,
            FakeTransactionManager(),
        )
        return use_case, ap_repository, matcher

    def execute(self, use_case):
        return use_case.execute(CreateAccountsPayableDTO(
            business_id=1,
            source_invoice_id=3,
            due_date=date(2026, 11, 15),
        ))

    def test_approved_and_matched_invoice_creates_open_payable_snapshot(self):
        use_case, repository, matcher = self.use_case()
        payable = self.execute(use_case)
        self.assertEqual(payable.status, AccountsPayableStatus.OPEN)
        self.assertEqual(payable.amount, Decimal("125.00"))
        self.assertEqual(payable.supplier_id, 2)
        self.assertEqual(payable.source_invoice_id, 3)
        self.assertEqual(payable.due_date, date(2026, 11, 15))
        self.assertEqual(repository.lock_calls, [(1, 3)])
        self.assertEqual(matcher.calls, [(1, 3, False)])

    def test_invoice_amount_changes_do_not_mutate_created_payable_snapshot(self):
        invoice = self.invoice()
        use_case, _, _ = self.use_case(invoice)
        payable = self.execute(use_case)
        invoice.items[0].unit_price = Decimal("99.00")
        self.assertEqual(invoice.total_price, Decimal("198.00"))
        self.assertEqual(payable.amount, Decimal("125.00"))

    def test_draft_invoice_is_rejected(self):
        use_case, _, matcher = self.use_case(self.invoice(PurchaseInvoiceStatus.DRAFT))
        with self.assertRaisesRegex(ValueError, "Only approved"):
            self.execute(use_case)
        self.assertEqual(matcher.calls, [])

    def test_all_non_matched_statuses_are_rejected(self):
        for match_status in (
            PurchaseInvoiceMatchingStatus.NOT_MATCHED,
            PurchaseInvoiceMatchingStatus.PENDING_RECEIPT,
            PurchaseInvoiceMatchingStatus.EXCEPTION,
        ):
            with self.subTest(status=match_status):
                use_case, repository, _ = self.use_case(matching_status=match_status)
                with self.assertRaisesRegex(ValueError, "current MATCHED"):
                    self.execute(use_case)
                self.assertIsNone(repository.created)

    def test_duplicate_payable_is_rejected_after_invoice_lock(self):
        use_case, repository, matcher = self.use_case(exists=True)
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.execute(use_case)
        self.assertEqual(repository.lock_calls, [(1, 3)])
        self.assertEqual(matcher.calls, [])

    def test_cross_business_invoice_is_not_found(self):
        use_case, _, _ = self.use_case(lock=False)
        with self.assertRaisesRegex(ValueError, "does not exist in this business"):
            use_case.execute(CreateAccountsPayableDTO(business_id=2, source_invoice_id=3))

    def test_supplier_must_belong_to_invoice_business(self):
        use_case, repository, _ = self.use_case(supplier_id=99)
        with self.assertRaisesRegex(ValueError, "supplier does not exist"):
            self.execute(use_case)
        self.assertIsNone(repository.created)
