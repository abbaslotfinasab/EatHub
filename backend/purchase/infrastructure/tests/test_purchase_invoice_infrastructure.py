from datetime import date, datetime, timezone
from decimal import Decimal
import inspect

from django.db import transaction
from django.test import TestCase

from accounts.models import Business, User
from inventory.models import Ingredient
from purchase.domain.entities.purchase_invoice import PurchaseInvoice, PurchaseInvoiceItem
from purchase.domain.enums.purchase_invoice_status import PurchaseInvoiceStatus
from purchase.domain.enums.purchase_invoice_match_exception import PurchaseInvoiceMatchException
from purchase.domain.enums.purchase_invoice_matching_status import PurchaseInvoiceMatchingStatus
from purchase.domain.services.purchase_invoice_matcher import PurchaseInvoiceMatcher
from purchase.infrastructure.persistence.django.repositories.purchase_invoice_repository import DjangoPurchaseInvoiceRepository
from purchase.infrastructure.persistence.django.repositories.purchase_invoice_matching_repository import DjangoPurchaseInvoiceMatchingRepository
from purchase.models import (
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseInvoice as DjangoPurchaseInvoice,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
)


class PurchaseInvoiceInfrastructureTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Invoice Business")
        self.other_business = Business.objects.create(name="Other Business")
        self.supplier = Supplier.objects.create(business=self.business, name="Supplier")
        self.other_supplier = Supplier.objects.create(business=self.other_business, name="Other")
        self.ingredient = Ingredient.objects.create(
            business=self.business, name="Flour", unit=Ingredient.Unit.KG,
        )
        self.other_ingredient = Ingredient.objects.create(
            business=self.other_business, name="Other Flour", unit=Ingredient.Unit.KG,
        )
        self.user = User.objects.create_user(
            email="invoice@example.com", password="password", name="Invoice", number="9001",
        )
        self.order = PurchaseOrder.objects.create(
            business=self.business, supplier=self.supplier,
            order_date=date(2026, 9, 1), status=PurchaseOrder.Status.SENT,
        )
        self.order_item = PurchaseOrderItem.objects.create(
            purchase_order=self.order, ingredient=self.ingredient,
            quantity=Decimal("100.000"), unit_price=Decimal("10.00"),
        )
        self.repository = DjangoPurchaseInvoiceRepository()

    def invoice(self, number="INV-1", quantity="30.000", ingredient_id=None, unit_price="12.00"):
        return PurchaseInvoice(
            id=None, business_id=self.business.id, supplier_id=self.supplier.id,
            invoice_number=number, invoice_date=date(2026, 9, 10),
            purchase_order_id=self.order.id,
            items=[PurchaseInvoiceItem(
                ingredient_id=ingredient_id or self.ingredient.id,
                quantity=Decimal(quantity), unit_price=Decimal(unit_price),
                purchase_order_item_id=self.order_item.id,
            )],
        )

    def receive(self, quantity="80.000", rejected="5.000"):
        receipt = GoodsReceipt.objects.create(
            business=self.business, purchase_order=self.order,
            received_by=self.user, received_date=datetime(2026, 9, 9, 12),
        )
        GoodsReceiptItem.objects.create(
            receipt=receipt, purchase_order_item=self.order_item,
            received_quantity=Decimal(quantity), rejected_quantity=Decimal(rejected),
        )

    def test_pre_receipt_invoice_is_persisted_and_price_variance_allowed(self):
        saved = self.repository.save(self.invoice())
        self.assertEqual(saved.items[0].unit_price, Decimal("12.00"))
        self.assertEqual(DjangoPurchaseInvoice.objects.count(), 1)

    def test_over_order_quantity_is_persisted_for_matching(self):
        saved = self.repository.save(self.invoice(quantity="100.001"))
        self.assertEqual(saved.items[0].quantity, Decimal("100.001"))

    def test_invoice_quantity_over_receipt_is_persisted_for_matching(self):
        self.receive()
        self.repository.save(self.invoice(number="INV-1", quantity="30.000"))
        self.repository.save(self.invoice(number="INV-2", quantity="50.000"))
        third = self.repository.save(self.invoice(number="INV-3", quantity="1.000"))
        self.assertEqual(third.items[0].quantity, Decimal("1.000"))

    def test_cross_business_ingredient_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invoice business"):
            self.repository.save(self.invoice(ingredient_id=self.other_ingredient.id))

    def test_duplicate_invoice_number_is_rejected(self):
        self.repository.save(self.invoice())
        with self.assertRaisesRegex(ValueError, "Invoice number"):
            self.repository.save(self.invoice())

    def test_invoice_defaults_to_draft_and_persists_approval_metadata(self):
        saved = self.repository.save(self.invoice())
        self.assertEqual(saved.status, PurchaseInvoiceStatus.DRAFT)

        saved.approve(self.user.id, datetime(2026, 9, 10, 12, 0))
        approved = self.repository.save_approved(saved)

        model = DjangoPurchaseInvoice.objects.get(id=approved.id)
        self.assertEqual(approved.status, PurchaseInvoiceStatus.APPROVED)
        self.assertEqual(model.approved_by_id, self.user.id)
        self.assertIsNotNone(model.approved_at)

    def test_repository_rejects_updates_to_approved_invoice(self):
        saved = self.repository.save(self.invoice())
        saved.approve(self.user.id, datetime(2026, 9, 10, 12, 0))
        self.repository.save_approved(saved)

        edited = self.invoice()
        edited.id = saved.id
        edited.invoice_number = "CHANGED"
        with self.assertRaisesRegex(ValueError, "can be modified"):
            self.repository.save(edited)

    def test_generic_save_cannot_bypass_atomic_posting_workflow(self):
        draft = self.repository.save(self.invoice())
        post_candidate = self.repository.get_by_id_for_business(draft.id, self.business.id)
        post_candidate.approve(self.user.id, datetime(2026, 9, 10, 12))
        post_candidate.post(self.user.id, datetime(2026, 9, 11, 12))

        with self.assertRaisesRegex(ValueError, "atomic posting workflow"):
            self.repository.save(post_candidate)

        stored = DjangoPurchaseInvoice.objects.get(id=draft.id)
        self.assertEqual(stored.status, DjangoPurchaseInvoice.Status.DRAFT)
        self.assertIsNone(stored.posted_at)

    def test_generic_save_cannot_bypass_approval_or_cancellation_workflows(self):
        draft = self.repository.save(self.invoice())
        approved_candidate = self.repository.get_by_id_for_business(draft.id, self.business.id)
        approved_candidate.approve(self.user.id, datetime(2026, 9, 10, 12))
        with self.assertRaisesRegex(ValueError, "dedicated workflow"):
            self.repository.save(approved_candidate)
        self.assertEqual(DjangoPurchaseInvoice.objects.get(id=draft.id).status, "draft")

        cancelled_candidate = self.repository.get_by_id_for_business(draft.id, self.business.id)
        cancelled_candidate.cancel(self.user.id, datetime(2026, 9, 11, 12), "duplicate")
        with self.assertRaisesRegex(ValueError, "dedicated workflow"):
            self.repository.save(cancelled_candidate)

    def test_repository_persists_cancellation_without_changing_financial_values(self):
        draft = self.repository.save(self.invoice())
        original_total = draft.total_price
        draft.cancel(self.user.id, datetime(2026, 9, 11, 12), "voided")
        cancelled = self.repository.save_cancelled(draft)
        self.assertEqual(cancelled.status, PurchaseInvoiceStatus.CANCELLED)
        self.assertEqual(cancelled.total_price, original_total)
        model = DjangoPurchaseInvoice.objects.get(id=cancelled.id)
        self.assertEqual(model.cancellation_reason, "voided")
        self.assertEqual(model.cancelled_by_id, self.user.id)

    def test_cancelled_and_posted_invoices_cannot_be_updated_or_reopened(self):
        draft = self.repository.save(self.invoice())
        draft.cancel(self.user.id, datetime(2026, 9, 11, 12), "voided")
        cancelled = self.repository.save_cancelled(draft)
        cancelled.invoice_number = "MUTATED"
        with self.assertRaisesRegex(ValueError, "Only draft"):
            self.repository.save(cancelled)

    def test_invoice_without_receipt_can_be_approved(self):
        saved = self.repository.save(self.invoice())
        saved.approve(self.user.id, datetime(2026, 9, 10, 12, 0))

        approved = self.repository.save_approved(saved)

        self.assertEqual(approved.status, PurchaseInvoiceStatus.APPROVED)

    def test_invoice_item_must_reference_item_on_invoice_purchase_order(self):
        other_order = PurchaseOrder.objects.create(
            business=self.business, supplier=self.supplier,
            order_date=date(2026, 9, 2), status=PurchaseOrder.Status.SENT,
        )
        other_item = PurchaseOrderItem.objects.create(
            purchase_order=other_order, ingredient=self.ingredient,
            quantity=Decimal("5"), unit_price=Decimal("10"),
        )
        invoice = self.invoice()
        invoice.items[0].purchase_order_item_id = other_item.id
        with self.assertRaisesRegex(ValueError, "does not belong"):
            self.repository.save(invoice)

    def test_cross_business_po_item_is_rejected(self):
        other_order = PurchaseOrder.objects.create(
            business=self.other_business, supplier=self.other_supplier,
            order_date=date(2026, 9, 2), status=PurchaseOrder.Status.SENT,
        )
        other_item = PurchaseOrderItem.objects.create(
            purchase_order=other_order, ingredient=self.other_ingredient,
            quantity=Decimal("5"), unit_price=Decimal("10"),
        )
        invoice = self.invoice()
        invoice.items[0].purchase_order_item_id = other_item.id
        with self.assertRaisesRegex(ValueError, "does not belong"):
            self.repository.save(invoice)

    def test_po_item_ingredient_mismatch_is_rejected(self):
        other_ingredient = Ingredient.objects.create(
            business=self.business, name="Sugar", unit=Ingredient.Unit.KG,
        )
        other_po_item = PurchaseOrderItem.objects.create(
            purchase_order=self.order, ingredient=other_ingredient,
            quantity=Decimal("5"), unit_price=Decimal("2"),
        )
        invoice = self.invoice()
        invoice.items[0].purchase_order_item_id = other_po_item.id
        with self.assertRaisesRegex(ValueError, "ingredient does not match"):
            self.repository.save(invoice)

    def test_duplicate_ingredient_po_items_are_explicitly_referenced(self):
        second_po_item = PurchaseOrderItem.objects.create(
            purchase_order=self.order, ingredient=self.ingredient,
            quantity=Decimal("50"), unit_price=Decimal("12"),
        )
        invoice = self.invoice()
        invoice.items.append(PurchaseInvoiceItem(
            ingredient_id=self.ingredient.id,
            purchase_order_item_id=second_po_item.id,
            quantity=Decimal("4"), unit_price=Decimal("12"),
        ))
        saved = self.repository.save(invoice)
        self.assertEqual(
            [item.purchase_order_item_id for item in saved.items],
            [self.order_item.id, second_po_item.id],
        )

    def test_matching_aggregates_receipts_and_previous_invoices_per_po_item(self):
        self.receive("70.000")
        self.receive("5.000")
        first = self.repository.save(self.invoice(number="INV-1", quantity="20.000", unit_price="10.00"))
        first.approve(self.user.id, datetime(2026, 9, 10, 12))
        self.repository.save_approved(first)
        second = self.repository.save(self.invoice(number="INV-2", quantity="10.000", unit_price="10.00"))
        second.approve(self.user.id, datetime(2026, 9, 10, 13))
        self.repository.save_approved(second)
        current = self.repository.save(self.invoice(number="INV-3", quantity="40.000", unit_price="10.00"))
        current.approve(self.user.id, datetime(2026, 9, 11, 12))
        current = self.repository.save_approved(current)
        context = DjangoPurchaseInvoiceMatchingRepository().load_matching_context(
            self.business.id, current.id,
        )
        self.assertEqual(context.lines[0].accepted_received_quantity, Decimal("75.000"))
        self.assertEqual(context.lines[0].previously_invoiced_quantity, Decimal("30.000"))
        self.assertEqual(context.lines[0].ordered_quantity, Decimal("100.000"))

    def test_approved_invoices_consume_quantity_cumulatively_and_current_is_excluded(self):
        self.receive("100.000", "0.000")
        repository = DjangoPurchaseInvoiceMatchingRepository()
        expected_previous = [Decimal("0"), Decimal("40.000"), Decimal("70.000"), Decimal("100.000")]
        expected_available = [Decimal("100.000"), Decimal("60.000"), Decimal("30.000"), Decimal("0.000")]
        for index, quantity in enumerate(("40.000", "30.000", "30.000", "1.000"), start=1):
            invoice = self.repository.save(self.invoice(
                number=f"SEQ-{index}", quantity=quantity, unit_price="10.00",
            ))
            invoice.approve(self.user.id, datetime(2026, 9, 10, 12 + index))
            invoice = self.repository.save_approved(invoice)
            context = repository.load_matching_context(self.business.id, invoice.id)
            line = context.lines[0]
            result = PurchaseInvoiceMatcher().match(context.invoice, list(context.lines))
            self.assertEqual(line.previously_invoiced_quantity, expected_previous[index - 1])
            self.assertEqual(
                line.accepted_received_quantity - line.previously_invoiced_quantity,
                expected_available[index - 1],
            )
            if index < 4:
                self.assertEqual(result.status, PurchaseInvoiceMatchingStatus.MATCHED)
            else:
                self.assertEqual(result.status, PurchaseInvoiceMatchingStatus.EXCEPTION)
                self.assertIn(PurchaseInvoiceMatchException.INVOICE_OVER_RECEIVED, result.exceptions)

    def test_multiple_receipts_count_received_quantity_and_exclude_rejected_quantity(self):
        self.receive("30.000", "0.000")
        self.receive("20.000", "0.000")
        self.receive("0.000", "50.000")
        invoice = self.repository.save(self.invoice(number="GR-AGG", quantity="50.000", unit_price="10.00"))
        context = DjangoPurchaseInvoiceMatchingRepository().load_matching_context(
            self.business.id, invoice.id,
        )
        self.assertEqual(context.lines[0].accepted_received_quantity, Decimal("50.000"))

    def test_matching_lock_query_targets_only_invoice_row_for_postgresql(self):
        # Source-structure guard only; SQLite cannot verify PostgreSQL row locking.
        method_source = inspect.getsource(
            DjangoPurchaseInvoiceMatchingRepository.lock_invoice_for_matching,
        )
        self.assertIn('select_for_update(of=("self",))', method_source)
        self.assertIn("business_id=business_id", method_source)
        self.assertNotIn("select_related", method_source)
        self.assertNotIn('"purchase_order"', method_source)

    def test_posting_lock_query_does_not_join_nullable_purchase_order(self):
        lock_source = inspect.getsource(self.repository.lock_for_posting)
        save_source = inspect.getsource(self.repository.save_posted)
        for source in (lock_source, save_source):
            self.assertIn('select_for_update(of=("self",))', source)
            self.assertNotIn("select_related", source)
            self.assertNotIn('"purchase_order"', source)
        self.assertIn("business_id=business_id", lock_source)

    def test_post_transition_persists_and_posted_invoices_consume_quantity(self):
        self.receive("100.000", "0.000")
        first = self.repository.save(self.invoice(number="POSTED-PREV", quantity="40.000", unit_price="10.00"))
        first.approve(self.user.id, datetime(2026, 9, 10, 12))
        first = self.repository.save_approved(first)
        posted_at = datetime(2026, 9, 11, 12, tzinfo=timezone.utc)

        with transaction.atomic():
            self.assertTrue(self.repository.lock_for_posting(self.business.id, first.id))
            first = self.repository.get_by_id_for_business(first.id, self.business.id)
            first.post(self.user.id, posted_at)
            first = self.repository.save_posted(first)

        self.assertEqual(first.status, PurchaseInvoiceStatus.POSTED)
        self.assertEqual(first.posted_by_id, self.user.id)
        self.assertEqual(first.posted_at, posted_at)
        current = self.repository.save(self.invoice(number="POSTED-CURRENT", quantity="30.000", unit_price="10.00"))
        current.approve(self.user.id, datetime(2026, 9, 12, 12))
        self.repository.save_approved(current)
        context = DjangoPurchaseInvoiceMatchingRepository().load_matching_context(
            self.business.id, current.id,
        )
        self.assertEqual(context.lines[0].previously_invoiced_quantity, Decimal("40.000"))

    def test_matching_context_is_tenant_scoped(self):
        invoice = self.repository.save(self.invoice())
        self.assertIsNone(DjangoPurchaseInvoiceMatchingRepository().load_matching_context(
            self.other_business.id, invoice.id,
        ))

    def test_matching_context_uses_constant_number_of_queries(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        invoice = self.repository.save(self.invoice())
        with CaptureQueriesContext(connection) as queries:
            DjangoPurchaseInvoiceMatchingRepository().load_matching_context(
                self.business.id, invoice.id,
            )
        self.assertLessEqual(len(queries), 5)
