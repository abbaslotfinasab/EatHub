from datetime import date
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.enums import RoleCode
from accounts.models import Business, Membership, Role, User
from inventory.models import Ingredient
from purchase.models import (
    AccountsPayable,
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseInvoice,
    PurchaseInvoiceItem,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
)


class AccountsPayableAPITests(APITestCase):
    endpoint = "/api/purchase/accounts-payables/"

    def setUp(self):
        self.user = User.objects.create_user(
            email="ap-api@example.com", password="password", name="AP API", number="9301",
        )
        self.business = Business.objects.create(name="AP API Business")
        self.other_business = Business.objects.create(name="Other AP API Business")
        role = Role.objects.create(business=self.business, name="Owner", code=RoleCode.OWNER)
        Membership.objects.create(user=self.user, business=self.business, role=role, is_active=True)
        self.supplier = Supplier.objects.create(business=self.business, name="Supplier")
        self.other_supplier = Supplier.objects.create(business=self.other_business, name="Other Supplier")
        self.ingredient = Ingredient.objects.create(
            business=self.business, name="Flour", unit=Ingredient.Unit.KG,
        )
        self.order = PurchaseOrder.objects.create(
            business=self.business,
            supplier=self.supplier,
            order_date=date(2026, 10, 1),
            status=PurchaseOrder.Status.SENT,
        )
        self.order_item = PurchaseOrderItem.objects.create(
            purchase_order=self.order,
            ingredient=self.ingredient,
            quantity=Decimal("100.000"),
            unit_price=Decimal("10.00"),
        )
        self.client.force_authenticate(self.user)

    def create_invoice(
        self,
        number="AP-API-1",
        *,
        invoice_status=PurchaseInvoice.Status.APPROVED,
        persisted_match="matched",
        quantity="2.000",
        invoice_price="10.00",
        accepted_quantity="2.000",
    ):
        approved = invoice_status == PurchaseInvoice.Status.APPROVED
        invoice = PurchaseInvoice.objects.create(
            business=self.business,
            supplier=self.supplier,
            purchase_order=self.order,
            invoice_number=number,
            invoice_date=date(2026, 10, 1),
            status=invoice_status,
            matching_status=persisted_match,
            approved_by=self.user if approved else None,
            approved_at="2026-10-01T12:00:00Z" if approved else None,
            subtotal=Decimal(quantity) * Decimal(invoice_price),
            total_price=Decimal(quantity) * Decimal(invoice_price),
        )
        PurchaseInvoiceItem.objects.create(
            purchase_invoice=invoice,
            ingredient=self.ingredient,
            purchase_order_item=self.order_item,
            quantity=Decimal(quantity),
            unit_price=Decimal(invoice_price),
            total_price=Decimal(quantity) * Decimal(invoice_price),
        )
        if accepted_quantity is not None:
            receipt = GoodsReceipt.objects.create(
                business=self.business,
                purchase_order=self.order,
                received_by=self.user,
                received_date="2026-10-02T12:00:00Z",
            )
            GoodsReceiptItem.objects.create(
                receipt=receipt,
                purchase_order_item=self.order_item,
                received_quantity=Decimal(accepted_quantity),
                rejected_quantity=Decimal("0"),
            )
        return invoice

    def test_post_creates_accounts_payable_from_currently_matched_invoice(self):
        invoice = self.create_invoice(persisted_match="not_matched")

        response = self.client.post(
            self.endpoint,
            {"source_invoice_id": invoice.id, "due_date": "2026-11-15"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payable = AccountsPayable.objects.get(source_invoice=invoice)
        self.assertEqual(payable.amount, Decimal("20.00"))
        self.assertEqual(payable.supplier_id, self.supplier.id)
        self.assertEqual(payable.business_id, self.business.id)
        self.assertEqual(payable.status, AccountsPayable.Status.OPEN)
        self.assertEqual(response.data["source_invoice_id"], invoice.id)
        self.assertEqual(response.data["amount"], "20.00")

    def test_post_rejects_draft_invoice(self):
        invoice = self.create_invoice(
            "AP-DRAFT",
            invoice_status=PurchaseInvoice.Status.DRAFT,
            persisted_match="matched",
        )
        response = self.client.post(self.endpoint, {"source_invoice_id": invoice.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_rejects_invoice_with_pending_receipt_result(self):
        invoice = self.create_invoice(
            "AP-PENDING",
            persisted_match="pending_receipt",
            accepted_quantity=None,
        )
        response = self.client.post(self.endpoint, {"source_invoice_id": invoice.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(AccountsPayable.objects.filter(source_invoice=invoice).exists())

    def test_post_rejects_stale_not_matched_state_when_current_match_is_not_matched(self):
        invoice = self.create_invoice(
            "AP-NOT-MATCHED",
            persisted_match="not_matched",
            accepted_quantity=None,
        )
        response = self.client.post(self.endpoint, {"source_invoice_id": invoice.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(AccountsPayable.objects.filter(source_invoice=invoice).exists())

    def test_post_rejects_invoice_with_exception_result(self):
        invoice = self.create_invoice(
            "AP-EXCEPTION",
            persisted_match="exception",
            invoice_price="10.01",
        )
        response = self.client.post(self.endpoint, {"source_invoice_id": invoice.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(AccountsPayable.objects.filter(source_invoice=invoice).exists())

    def test_cross_business_invoice_is_hidden(self):
        other_order = PurchaseOrder.objects.create(
            business=self.other_business,
            supplier=self.other_supplier,
            order_date=date(2026, 10, 1),
            status=PurchaseOrder.Status.SENT,
        )
        other_invoice = PurchaseInvoice.objects.create(
            business=self.other_business,
            supplier=self.other_supplier,
            purchase_order=other_order,
            invoice_number="OTHER-AP",
            invoice_date=date(2026, 10, 1),
            status=PurchaseInvoice.Status.APPROVED,
            approved_by=self.user,
            approved_at="2026-10-01T12:00:00Z",
            subtotal=Decimal("10.00"),
            total_price=Decimal("10.00"),
        )
        response = self.client.post(
            self.endpoint, {"source_invoice_id": other_invoice.id}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_duplicate_accounts_payable_is_rejected(self):
        invoice = self.create_invoice("AP-DUP")
        payload = {"source_invoice_id": invoice.id}
        self.assertEqual(self.client.post(self.endpoint, payload, format="json").status_code, 201)
        self.assertEqual(self.client.post(self.endpoint, payload, format="json").status_code, 400)
        self.assertEqual(AccountsPayable.objects.filter(source_invoice=invoice).count(), 1)

    def test_client_cannot_control_business_supplier_amount_status_or_lifecycle_fields(self):
        invoice = self.create_invoice("AP-WRITE-PROTECT")
        protected = {
            "business_id": self.other_business.id,
            "supplier_id": self.other_supplier.id,
            "amount": "0.01",
            "status": "paid",
            "posted_at": "2026-10-03T12:00:00Z",
            "posted_by_id": self.user.id,
            "cancelled_at": "2026-10-03T12:00:00Z",
            "cancelled_by_id": self.user.id,
        }
        for field, value in protected.items():
            with self.subTest(field=field):
                response = self.client.post(
                    self.endpoint,
                    {"source_invoice_id": invoice.id, field: value},
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(AccountsPayable.objects.filter(source_invoice=invoice).exists())

    def test_list_is_scoped_to_active_business_and_detail_is_tenant_scoped(self):
        invoice = self.create_invoice("AP-LIST")
        created = self.client.post(
            self.endpoint, {"source_invoice_id": invoice.id}, format="json",
        )
        listing = self.client.get(self.endpoint)
        detail = self.client.get(f"{self.endpoint}{created.data['id']}/")
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in listing.data], [created.data["id"]])
        self.assertEqual(detail.status_code, status.HTTP_200_OK)

        other_invoice = PurchaseInvoice.objects.create(
            business=self.other_business,
            supplier=self.other_supplier,
            invoice_number="OTHER-AP-LIST",
            invoice_date=date(2026, 10, 1),
            subtotal=Decimal("5.00"),
            total_price=Decimal("5.00"),
        )
        other_payable = AccountsPayable.objects.create(
            business=self.other_business,
            supplier=self.other_supplier,
            source_invoice=other_invoice,
            amount=Decimal("5.00"),
        )
        self.assertEqual(self.client.get(self.endpoint).data.__len__(), 1)
        self.assertEqual(
            self.client.get(f"{self.endpoint}{other_payable.id}/").status_code,
            status.HTTP_404_NOT_FOUND,
        )
