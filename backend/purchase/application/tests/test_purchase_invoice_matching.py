from contextlib import nullcontext
from datetime import date, datetime, timezone
from decimal import Decimal

from django.test import SimpleTestCase

from purchase.application.dto.purchase_invoice_matching import PurchaseInvoiceMatchingContext
from purchase.application.use_cases.purchase_invoice.match_purchase_invoice import MatchPurchaseInvoiceUseCase
from purchase.domain.entities.purchase_invoice import PurchaseInvoice, PurchaseInvoiceItem
from purchase.domain.enums.purchase_invoice_match_exception import PurchaseInvoiceMatchException
from purchase.domain.enums.purchase_invoice_matching_status import PurchaseInvoiceMatchingStatus
from purchase.domain.enums.purchase_invoice_status import PurchaseInvoiceStatus
from purchase.domain.services.purchase_invoice_matcher import PurchaseInvoiceMatchLineInput


class FakeTransactionManager:
    def atomic(self):
        return nullcontext()


class FakeMatchingRepository:
    def __init__(self, context):
        self.context = context
        self.saved = None
        self.calls = []

    def lock_invoice_for_matching(self, business_id, invoice_id):
        self.calls.append("lock")
        return self.context.invoice.business_id == business_id and self.context.invoice.id == invoice_id

    def load_matching_context(self, business_id, invoice_id):
        self.calls.append("load")
        if self.context.invoice.business_id != business_id or self.context.invoice.id != invoice_id:
            return None
        return self.context

    def save_matching_state(self, business_id, invoice_id, status, matched_at):
        self.saved = (business_id, invoice_id, status, matched_at)


class MatchPurchaseInvoiceUseCaseTests(SimpleTestCase):
    def context(self, status=PurchaseInvoiceStatus.APPROVED):
        invoice = PurchaseInvoice(
            id=5, business_id=1, supplier_id=2, invoice_number="INV-5",
            invoice_date=date(2026, 10, 1), purchase_order_id=9,
            status=status,
            approved_by_id=7 if status == PurchaseInvoiceStatus.APPROVED else None,
            approved_at=datetime(2026, 10, 1) if status == PurchaseInvoiceStatus.APPROVED else None,
            items=[PurchaseInvoiceItem(
                ingredient_id=3, purchase_order_item_id=10,
                quantity=Decimal("2"), unit_price=Decimal("10"), id=11,
            )],
        )
        line = PurchaseInvoiceMatchLineInput(
            invoice_item_id=11, purchase_order_item_id=10,
            ordered_quantity=Decimal("10"), accepted_received_quantity=Decimal("0"),
            previously_invoiced_quantity=Decimal("0"), current_invoice_quantity=Decimal("2"),
            purchase_order_unit_price=Decimal("10"), invoice_unit_price=Decimal("10"),
        )
        return PurchaseInvoiceMatchingContext(
            invoice=invoice, lines=(line,),
            matching_status=PurchaseInvoiceMatchingStatus.NOT_MATCHED,
            matched_at=None,
        )

    def test_draft_invoice_is_rejected(self):
        repository = FakeMatchingRepository(self.context(PurchaseInvoiceStatus.DRAFT))
        use_case = MatchPurchaseInvoiceUseCase(repository, FakeTransactionManager())
        with self.assertRaisesRegex(ValueError, "Only approved"):
            use_case.execute(1, 5)
        self.assertIsNone(repository.saved)

    def test_approved_invoice_matches_and_persists_status_and_timestamp(self):
        repository = FakeMatchingRepository(self.context())
        matched_at = datetime(2026, 10, 2, tzinfo=timezone.utc)
        use_case = MatchPurchaseInvoiceUseCase(
            repository, FakeTransactionManager(), clock=lambda: matched_at,
        )
        result = use_case.execute(1, 5)
        self.assertEqual(result.current.status, PurchaseInvoiceMatchingStatus.PENDING_RECEIPT)
        self.assertIn(PurchaseInvoiceMatchException.RECEIPT_PENDING, result.current.exceptions)
        self.assertEqual(repository.saved, (1, 5, result.current.status, matched_at))
        self.assertEqual(repository.calls, ["lock", "load"])
        self.assertEqual(result.last_persisted.status, result.current.status)
        self.assertEqual(result.last_persisted.matched_at, matched_at)

    def test_get_style_recalculation_does_not_persist(self):
        repository = FakeMatchingRepository(self.context())
        result = MatchPurchaseInvoiceUseCase(repository, FakeTransactionManager()).execute(
            1, 5, persist=False,
        )
        self.assertEqual(result.current.status, PurchaseInvoiceMatchingStatus.PENDING_RECEIPT)
        self.assertIsNone(repository.saved)
        self.assertEqual(repository.calls, ["load"])
        self.assertEqual(result.last_persisted.status, PurchaseInvoiceMatchingStatus.NOT_MATCHED)
        self.assertIsNone(result.last_persisted.matched_at)

    def test_tenant_scoping_hides_invoice(self):
        repository = FakeMatchingRepository(self.context())
        with self.assertRaisesRegex(ValueError, "does not exist"):
            MatchPurchaseInvoiceUseCase(repository, FakeTransactionManager()).execute(99, 5)
