from datetime import date, datetime
from decimal import Decimal

from django.test import SimpleTestCase

from purchase.domain.entities.purchase_invoice import PurchaseInvoice, PurchaseInvoiceItem
from purchase.domain.enums.purchase_invoice_status import PurchaseInvoiceStatus


class PurchaseInvoiceDomainTests(SimpleTestCase):
    def item(self, **kwargs):
        values = {
            "ingredient_id": 1,
            "quantity": Decimal("3.000"),
            "unit_price": Decimal("10.00"),
            "purchase_order_item_id": 1,
        }
        values.update(kwargs)
        return PurchaseInvoiceItem(**values)

    def invoice(self, **kwargs):
        values = {
            "id": None,
            "business_id": 1,
            "supplier_id": 1,
            "invoice_number": "INV-1",
            "invoice_date": date(2026, 9, 10),
            "purchase_order_id": 1,
            "items": [self.item()],
        }
        values.update(kwargs)
        return PurchaseInvoice(**values)

    def test_calculates_item_and_invoice_amounts_with_rounding(self):
        invoice = self.invoice(
            items=[self.item(discount_percent=Decimal("10"), tax_percent=Decimal("5"))],
            discount_percent=Decimal("10"),
            tax_percent=Decimal("20"),
        )
        self.assertEqual(invoice.items[0].line_subtotal, Decimal("30.00"))
        self.assertEqual(invoice.items[0].discount_amount, Decimal("3.00"))
        self.assertEqual(invoice.items[0].tax_amount, Decimal("1.35"))
        self.assertEqual(invoice.items[0].total_price, Decimal("28.35"))
        self.assertEqual(invoice.subtotal, Decimal("30.00"))
        self.assertEqual(invoice.total_item_discount, Decimal("3.00"))
        self.assertEqual(invoice.total_item_tax, Decimal("1.35"))
        self.assertEqual(invoice.discount_amount, Decimal("3.00"))
        self.assertEqual(invoice.tax_amount, Decimal("4.80"))
        self.assertEqual(invoice.total_price, Decimal("30.15"))

    def test_no_discounts_or_taxes(self):
        invoice = self.invoice()
        self.assertEqual(invoice.subtotal, Decimal("30.00"))
        self.assertEqual(invoice.total_item_discount, Decimal("0.00"))
        self.assertEqual(invoice.total_item_tax, Decimal("0.00"))
        self.assertEqual(invoice.discount_amount, Decimal("0.00"))
        self.assertEqual(invoice.tax_amount, Decimal("0.00"))
        self.assertEqual(invoice.total_price, Decimal("30.00"))

    def test_item_discount_only(self):
        invoice = self.invoice(items=[self.item(discount_percent=Decimal("10"))])
        self.assertEqual(invoice.subtotal, Decimal("30.00"))
        self.assertEqual(invoice.total_item_discount, Decimal("3.00"))
        self.assertEqual(invoice.total_item_tax, Decimal("0.00"))
        self.assertEqual(invoice.total_price, Decimal("27.00"))

    def test_item_tax_only(self):
        invoice = self.invoice(items=[self.item(tax_percent=Decimal("10"))])
        self.assertEqual(invoice.subtotal, Decimal("30.00"))
        self.assertEqual(invoice.total_item_discount, Decimal("0.00"))
        self.assertEqual(invoice.total_item_tax, Decimal("3.00"))
        self.assertEqual(invoice.total_price, Decimal("33.00"))

    def test_invoice_discount_only(self):
        invoice = self.invoice(discount_percent=Decimal("10"))
        self.assertEqual(invoice.subtotal, Decimal("30.00"))
        self.assertEqual(invoice.discount_amount, Decimal("3.00"))
        self.assertEqual(invoice.tax_amount, Decimal("0.00"))
        self.assertEqual(invoice.total_price, Decimal("27.00"))

    def test_invoice_tax_only(self):
        invoice = self.invoice(tax_percent=Decimal("10"))
        self.assertEqual(invoice.subtotal, Decimal("30.00"))
        self.assertEqual(invoice.discount_amount, Decimal("0.00"))
        self.assertEqual(invoice.tax_amount, Decimal("3.00"))
        self.assertEqual(invoice.total_price, Decimal("33.00"))

    def test_multiple_items_and_final_reconciliation(self):
        invoice = self.invoice(
            items=[
                self.item(quantity=Decimal("1.000"), unit_price=Decimal("10.00"), discount_percent=Decimal("10"), tax_percent=Decimal("5")),
                self.item(ingredient_id=2, quantity=Decimal("2.000"), unit_price=Decimal("7.00"), discount_percent=Decimal("5"), tax_percent=Decimal("10")),
            ],
            discount_percent=Decimal("10"),
            tax_percent=Decimal("20"),
        )
        self.assertEqual(invoice.subtotal, Decimal("24.00"))
        self.assertEqual(invoice.total_item_discount, Decimal("1.70"))
        self.assertEqual(invoice.total_item_tax, Decimal("1.78"))
        self.assertEqual(invoice.discount_amount, Decimal("2.40"))
        self.assertEqual(invoice.tax_amount, Decimal("3.98"))
        self.assertEqual(invoice.total_price, Decimal("25.66"))

    def test_rounding_is_applied_at_item_and_invoice_levels(self):
        invoice = self.invoice(
            items=[self.item(quantity=Decimal("3.000"), unit_price=Decimal("0.05"), discount_percent=Decimal("33.33"), tax_percent=Decimal("7.77"))],
            discount_percent=Decimal("12.34"),
            tax_percent=Decimal("8.88"),
        )
        self.assertEqual(invoice.subtotal, Decimal("0.15"))
        self.assertEqual(invoice.total_item_discount, Decimal("0.05"))
        self.assertEqual(invoice.total_item_tax, Decimal("0.01"))
        self.assertEqual(invoice.discount_amount, Decimal("0.02"))
        self.assertEqual(invoice.tax_amount, Decimal("0.01"))
        self.assertEqual(invoice.total_price, Decimal("0.10"))

    def test_requires_purchase_order_and_items(self):
        with self.assertRaisesRegex(ValueError, "purchase order"):
            self.invoice(purchase_order_id=None)
        with self.assertRaisesRegex(ValueError, "at least one item"):
            self.invoice(items=[])

    def test_rejects_invalid_item_values(self):
        with self.assertRaises(ValueError):
            self.item(quantity=Decimal("0"))
        with self.assertRaises(ValueError):
            self.item(unit_price=Decimal("-1"))

    def test_purchase_order_item_id_must_be_positive(self):
        with self.assertRaisesRegex(ValueError, "Purchase order item ID"):
            self.item(purchase_order_item_id=0)

    def test_duplicate_ingredients_are_allowed(self):
        invoice = self.invoice(items=[self.item(), self.item(purchase_order_item_id=2)])
        self.assertEqual(len(invoice.items), 2)

    def test_same_purchase_order_item_cannot_appear_twice(self):
        with self.assertRaisesRegex(ValueError, "only appear once"):
            self.invoice(items=[self.item(), self.item(quantity=Decimal("4"))])

    def test_distinct_purchase_order_items_are_allowed(self):
        invoice = self.invoice(items=[
            self.item(purchase_order_item_id=1),
            self.item(ingredient_id=2, purchase_order_item_id=2),
        ])
        self.assertEqual([item.purchase_order_item_id for item in invoice.items], [1, 2])

    def test_purchase_order_item_reference_requires_matching_order_and_ingredient(self):
        invoice = self.invoice()
        invoice.validate_purchase_order_item_references(
            purchase_order_id=1,
            purchase_order_business_id=1,
            item_ingredient_ids={1: 1},
        )
        with self.assertRaisesRegex(ValueError, "does not match"):
            invoice.validate_purchase_order_item_references(
                purchase_order_id=1,
                purchase_order_business_id=1,
                item_ingredient_ids={1: 2},
            )
        with self.assertRaisesRegex(ValueError, "does not belong"):
            invoice.validate_purchase_order_item_references(
                purchase_order_id=2,
                purchase_order_business_id=1,
                item_ingredient_ids={1: 1},
            )

    def test_new_invoice_defaults_to_draft(self):
        self.assertEqual(self.invoice().status, PurchaseInvoiceStatus.DRAFT)

    def test_draft_can_be_approved_with_metadata(self):
        invoice = self.invoice()
        approved_at = datetime(2026, 9, 10, 12, 0)

        invoice.approve(approved_by_id=7, approved_at=approved_at)

        self.assertEqual(invoice.status, PurchaseInvoiceStatus.APPROVED)
        self.assertEqual(invoice.approved_by_id, 7)
        self.assertEqual(invoice.approved_at, approved_at)

    def test_approved_invoice_cannot_be_approved_again(self):
        invoice = self.invoice()
        invoice.approve(7, datetime(2026, 9, 10, 12, 0))

        with self.assertRaisesRegex(ValueError, "cannot be approved"):
            invoice.approve(8, datetime(2026, 9, 10, 13, 0))

    def test_approved_invoice_cannot_be_modified(self):
        invoice = self.invoice()
        invoice.approve(7, datetime(2026, 9, 10, 12, 0))

        with self.assertRaisesRegex(ValueError, "cannot be modified"):
            invoice.add_item(2, Decimal("1.000"), Decimal("2.00"), 1)

    def test_approval_requires_valid_actor_and_timestamp(self):
        invoice = self.invoice()

        with self.assertRaisesRegex(ValueError, "actor"):
            invoice.approve(0, datetime(2026, 9, 10, 12, 0))
        with self.assertRaisesRegex(ValueError, "timestamp"):
            invoice.approve(7, None)
