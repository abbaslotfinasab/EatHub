from datetime import date, datetime
from decimal import Decimal

from django.test import TestCase

from accounts.models import Business, User
from inventory.models import Ingredient
from purchase.domain.entities.purchase_invoice import PurchaseInvoice, PurchaseInvoiceItem
from purchase.domain.enums.purchase_invoice_status import PurchaseInvoiceStatus
from purchase.infrastructure.persistence.django.repositories.purchase_invoice_repository import DjangoPurchaseInvoiceRepository
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
            )],
        )

    def receive(self, quantity="80.000"):
        receipt = GoodsReceipt.objects.create(
            business=self.business, purchase_order=self.order,
            received_by=self.user, received_date=datetime(2026, 9, 9, 12),
        )
        GoodsReceiptItem.objects.create(
            receipt=receipt, purchase_order_item=self.order_item,
            received_quantity=Decimal(quantity), rejected_quantity=Decimal("5.000"),
        )

    def test_pre_receipt_invoice_is_persisted_and_price_variance_allowed(self):
        saved = self.repository.save(self.invoice())
        self.assertEqual(saved.items[0].unit_price, Decimal("12.00"))
        self.assertEqual(DjangoPurchaseInvoice.objects.count(), 1)

    def test_cumulative_received_quantity_limits_multiple_invoices(self):
        self.receive()
        self.repository.save(self.invoice(number="INV-1", quantity="30.000"))
        self.repository.save(self.invoice(number="INV-2", quantity="50.000"))
        with self.assertRaisesRegex(ValueError, "accepted received"):
            self.repository.save(self.invoice(number="INV-3", quantity="1.000"))

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
        approved = self.repository.save(saved)

        model = DjangoPurchaseInvoice.objects.get(id=approved.id)
        self.assertEqual(approved.status, PurchaseInvoiceStatus.APPROVED)
        self.assertEqual(model.approved_by_id, self.user.id)
        self.assertIsNotNone(model.approved_at)

    def test_repository_rejects_updates_to_approved_invoice(self):
        saved = self.repository.save(self.invoice())
        saved.approve(self.user.id, datetime(2026, 9, 10, 12, 0))
        self.repository.save(saved)

        edited = self.invoice()
        edited.id = saved.id
        edited.invoice_number = "CHANGED"
        with self.assertRaisesRegex(ValueError, "cannot be modified"):
            self.repository.save(edited)

    def test_invoice_without_receipt_can_be_approved(self):
        saved = self.repository.save(self.invoice())
        saved.approve(self.user.id, datetime(2026, 9, 10, 12, 0))

        approved = self.repository.save(saved)

        self.assertEqual(approved.status, PurchaseInvoiceStatus.APPROVED)
