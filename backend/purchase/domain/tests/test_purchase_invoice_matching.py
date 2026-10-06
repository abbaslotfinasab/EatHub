from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase

from purchase.domain.entities.purchase_invoice import PurchaseInvoice, PurchaseInvoiceItem
from purchase.domain.enums.purchase_invoice_match_exception import PurchaseInvoiceMatchException
from purchase.domain.enums.purchase_invoice_matching_status import PurchaseInvoiceMatchingStatus
from purchase.domain.services.purchase_invoice_matcher import (
    PurchaseInvoiceMatchLineInput,
    PurchaseInvoiceMatcher,
)


class PurchaseInvoiceMatcherTests(SimpleTestCase):
    def setUp(self):
        self.invoice = PurchaseInvoice(
            id=4,
            business_id=1,
            supplier_id=2,
            invoice_number="INV-4",
            invoice_date=date(2026, 10, 1),
            purchase_order_id=9,
            items=[PurchaseInvoiceItem(
                ingredient_id=10,
                purchase_order_item_id=20,
                quantity=Decimal("30"),
                unit_price=Decimal("100"),
                id=30,
            )],
        )
        self.base = dict(
            invoice_item_id=30,
            purchase_order_item_id=20,
            ordered_quantity=Decimal("100"),
            accepted_received_quantity=Decimal("0"),
            previously_invoiced_quantity=Decimal("0"),
            current_invoice_quantity=Decimal("30"),
            purchase_order_unit_price=Decimal("100"),
            invoice_unit_price=Decimal("100"),
        )
        self.matcher = PurchaseInvoiceMatcher()

    def match(self, **overrides):
        values = {**self.base, **overrides}
        return self.matcher.match(self.invoice, [PurchaseInvoiceMatchLineInput(**values)])

    def test_no_receipt_is_pending(self):
        result = self.match()
        self.assertEqual(result.status, PurchaseInvoiceMatchingStatus.PENDING_RECEIPT)
        self.assertEqual(result.exceptions, (PurchaseInvoiceMatchException.RECEIPT_PENDING,))

    def test_accepted_partial_receipt_matches_within_available_quantity(self):
        result = self.match(accepted_received_quantity=Decimal("70"))
        self.assertEqual(result.status, PurchaseInvoiceMatchingStatus.MATCHED)
        self.assertEqual(result.lines[0].available_quantity, Decimal("70"))

    def test_previous_invoicing_reduces_available_quantity(self):
        result = self.match(
            accepted_received_quantity=Decimal("70"),
            previously_invoiced_quantity=Decimal("20"),
            current_invoice_quantity=Decimal("50"),
        )
        self.assertEqual(result.status, PurchaseInvoiceMatchingStatus.MATCHED)
        self.assertEqual(result.lines[0].available_quantity, Decimal("50"))

    def test_excess_over_available_is_exception(self):
        result = self.match(
            accepted_received_quantity=Decimal("70"),
            previously_invoiced_quantity=Decimal("20"),
            current_invoice_quantity=Decimal("51"),
        )
        self.assertEqual(result.status, PurchaseInvoiceMatchingStatus.EXCEPTION)
        self.assertIn(PurchaseInvoiceMatchException.INVOICE_OVER_RECEIVED, result.exceptions)

    def test_no_receipt_is_not_reported_as_overreceived(self):
        result = self.match(current_invoice_quantity=Decimal("100"))
        self.assertEqual(result.exceptions, (PurchaseInvoiceMatchException.RECEIPT_PENDING,))

    def test_price_match_has_no_variance(self):
        result = self.match(accepted_received_quantity=Decimal("30"))
        self.assertEqual(result.lines[0].price_variance, Decimal("0"))
        self.assertNotIn(PurchaseInvoiceMatchException.PRICE_VARIANCE, result.exceptions)

    def test_price_variance_causes_exception_without_rejecting_quantity(self):
        result = self.match(
            accepted_received_quantity=Decimal("30"),
            invoice_unit_price=Decimal("105"),
        )
        self.assertEqual(result.status, PurchaseInvoiceMatchingStatus.EXCEPTION)
        self.assertEqual(result.lines[0].available_quantity, Decimal("30"))
        self.assertIn(PurchaseInvoiceMatchException.PRICE_VARIANCE, result.exceptions)

    def test_rejected_quantity_is_not_part_of_match_input_or_available_quantity(self):
        result = self.match(accepted_received_quantity=Decimal("80"))
        self.assertEqual(result.lines[0].available_quantity, Decimal("80"))

    def test_empty_inputs_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least one item"):
            self.matcher.match(self.invoice, [])
