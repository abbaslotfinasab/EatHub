from contextlib import nullcontext
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase

from purchase.application.dto.purchase_invoice_posting import PostPurchaseInvoiceDTO
from purchase.application.use_cases.purchase_invoice.post_purchase_invoice import PostPurchaseInvoice
from purchase.domain.entities.accounts_payable import AccountsPayable
from purchase.domain.entities.purchase_invoice import PurchaseInvoice, PurchaseInvoiceItem
from purchase.domain.enums.accounts_payable_status import AccountsPayableStatus
from purchase.domain.enums.purchase_invoice_matching_status import PurchaseInvoiceMatchingStatus
from purchase.domain.enums.purchase_invoice_status import PurchaseInvoiceStatus


class FakeTransactionManager:
    def atomic(self):
        return nullcontext()


class FakeInvoiceRepository:
    def __init__(self, invoice, *, lock=True, fail_save=False):
        self.invoice = invoice
        self.lock = lock
        self.fail_save = fail_save
        self.calls = []

    def lock_for_posting(self, business_id, invoice_id):
        self.calls.append("lock")
        return self.lock and self.invoice.id == invoice_id and self.invoice.business_id == business_id

    def get_by_id_for_business(self, invoice_id, business_id):
        self.calls.append("get")
        if self.invoice.id != invoice_id or self.invoice.business_id != business_id:
            return None
        return self.invoice

    def save_posted(self, invoice):
        self.calls.append("save_posted")
        if self.fail_save:
            raise ValueError("forced invoice persistence failure")
        self.invoice = invoice
        return invoice


class FakeAccountsPayableRepository:
    def __init__(self, *, exists=False, fail_create=False):
        self.exists = exists
        self.fail_create = fail_create
        self.created = None

    def exists_for_source_invoice(self, invoice_id, business_id):
        return self.exists

    def create(self, payable):
        if self.fail_create:
            raise ValueError("forced AP persistence failure")
        payable.id = 30
        self.created = payable
        return payable


class FakeMatcher:
    def __init__(self, status=PurchaseInvoiceMatchingStatus.MATCHED):
        self.status = status
        self.calls = []

    def execute(self, business_id, invoice_id, *, persist):
        self.calls.append((business_id, invoice_id, persist))
        return SimpleNamespace(
            current=SimpleNamespace(status=self.status),
            last_persisted=SimpleNamespace(matched_at=datetime(2026, 10, 7, tzinfo=timezone.utc)),
        )


class PurchaseInvoicePostingUseCaseTests(SimpleTestCase):
    def invoice(self, status=PurchaseInvoiceStatus.APPROVED):
        is_approved = status in (PurchaseInvoiceStatus.APPROVED, PurchaseInvoiceStatus.POSTED)
        return PurchaseInvoice(
            id=10,
            business_id=1,
            supplier_id=2,
            invoice_number="INV-10",
            invoice_date=date(2026, 10, 1),
            purchase_order_id=5,
            status=status,
            approved_by_id=9 if is_approved else None,
            approved_at=datetime(2026, 10, 2) if is_approved else None,
            posted_by_id=9 if status == PurchaseInvoiceStatus.POSTED else None,
            posted_at=datetime(2026, 10, 3) if status == PurchaseInvoiceStatus.POSTED else None,
            items=[PurchaseInvoiceItem(
                ingredient_id=3,
                quantity=Decimal("2"),
                unit_price=Decimal("12.50"),
                purchase_order_item_id=6,
            )],
        )

    def setup_use_case(self, *, invoice=None, match_status=PurchaseInvoiceMatchingStatus.MATCHED,
                       ap_exists=False, ap_fail=False, invoice_save_fail=False, lock=True):
        invoice_repo = FakeInvoiceRepository(invoice or self.invoice(), lock=lock, fail_save=invoice_save_fail)
        ap_repo = FakeAccountsPayableRepository(exists=ap_exists, fail_create=ap_fail)
        matcher = FakeMatcher(match_status)
        use_case = PostPurchaseInvoice(
            invoice_repo, ap_repo, matcher, FakeTransactionManager(),
        )
        return use_case, invoice_repo, ap_repo, matcher

    def command(self, business_id=1):
        return PostPurchaseInvoiceDTO(
            business_id=business_id,
            purchase_invoice_id=10,
            posted_by_id=7,
            posted_at=datetime(2026, 10, 7, tzinfo=timezone.utc),
            due_date=date(2026, 11, 15),
        )

    def test_approved_currently_matched_invoice_creates_ap_and_posts(self):
        use_case, invoice_repo, ap_repo, matcher = self.setup_use_case()
        result = use_case.execute(self.command())
        self.assertEqual(result.invoice.status, PurchaseInvoiceStatus.POSTED)
        self.assertEqual(result.invoice.posted_by_id, 7)
        self.assertEqual(result.invoice.posted_at, self.command().posted_at)
        self.assertEqual(result.invoice.matching_status, PurchaseInvoiceMatchingStatus.MATCHED)
        self.assertEqual(result.accounts_payable.status, AccountsPayableStatus.OPEN)
        self.assertEqual(result.accounts_payable.business_id, 1)
        self.assertEqual(result.accounts_payable.supplier_id, 2)
        self.assertEqual(result.accounts_payable.source_invoice_id, 10)
        self.assertEqual(result.accounts_payable.amount, Decimal("25.00"))
        self.assertEqual(result.accounts_payable.due_date, date(2026, 11, 15))
        self.assertIs(ap_repo.created, result.accounts_payable)
        self.assertEqual(matcher.calls, [(1, 10, True)])
        self.assertEqual(invoice_repo.calls, ["lock", "get", "save_posted"])

    def test_current_matching_result_is_used_instead_of_persisted_status(self):
        invoice = self.invoice()
        invoice.matching_status = PurchaseInvoiceMatchingStatus.PENDING_RECEIPT
        use_case, _, ap_repo, matcher = self.setup_use_case(invoice=invoice)
        use_case.execute(self.command())
        self.assertEqual(matcher.calls, [(1, 10, True)])
        self.assertEqual(ap_repo.created.status, AccountsPayableStatus.OPEN)

    def test_non_matched_current_results_are_rejected(self):
        for match_status in (
            PurchaseInvoiceMatchingStatus.NOT_MATCHED,
            PurchaseInvoiceMatchingStatus.PENDING_RECEIPT,
            PurchaseInvoiceMatchingStatus.EXCEPTION,
        ):
            with self.subTest(status=match_status):
                use_case, _, ap_repo, _ = self.setup_use_case(match_status=match_status)
                with self.assertRaisesRegex(ValueError, "current MATCHED"):
                    use_case.execute(self.command())
                self.assertIsNone(ap_repo.created)

    def test_draft_posted_and_other_lifecycle_states_are_rejected(self):
        for state in (PurchaseInvoiceStatus.DRAFT, PurchaseInvoiceStatus.POSTED, "cancelled"):
            with self.subTest(status=state):
                invoice = self.invoice(state) if state != "cancelled" else self.invoice()
                if state == "cancelled":
                    invoice.status = state
                use_case, _, ap_repo, matcher = self.setup_use_case(invoice=invoice)
                with self.assertRaisesRegex(ValueError, "Only approved"):
                    use_case.execute(self.command())
                self.assertIsNone(ap_repo.created)
                self.assertEqual(matcher.calls, [])

    def test_cross_business_invoice_is_hidden(self):
        use_case, _, ap_repo, _ = self.setup_use_case(lock=False)
        with self.assertRaisesRegex(ValueError, "does not exist in this business"):
            use_case.execute(self.command(business_id=2))
        self.assertIsNone(ap_repo.created)

    def test_existing_ap_is_rejected(self):
        use_case, _, ap_repo, _ = self.setup_use_case(ap_exists=True)
        with self.assertRaisesRegex(ValueError, "already exists"):
            use_case.execute(self.command())
        self.assertIsNone(ap_repo.created)

    def test_ap_creation_failure_never_posts_invoice(self):
        use_case, invoice_repo, ap_repo, _ = self.setup_use_case(ap_fail=True)
        with self.assertRaisesRegex(ValueError, "AP persistence failure"):
            use_case.execute(self.command())
        self.assertEqual(invoice_repo.invoice.status, PurchaseInvoiceStatus.APPROVED)
        self.assertIsNone(ap_repo.created)
