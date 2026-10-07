from datetime import date
from decimal import Decimal
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.enums import RoleCode
from accounts.models import Business, Membership, Role, User
from inventory.models import Ingredient
from purchase.models import (
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseInvoice as DjangoPurchaseInvoice,
    PurchaseInvoiceItem,
    AccountsPayable,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
    SupplierPayment,
    PaymentAllocation,
)


class PurchaseInvoiceAPITests(APITestCase):
    endpoint = "/api/purchase/purchase-invoices/"

    def setUp(self):
        self.user = User.objects.create_user(
            email="invoice-api@example.com", password="password", name="API", number="9101",
        )
        self.business = Business.objects.create(name="API Business")
        self.other_business = Business.objects.create(name="Other API Business")
        role = Role.objects.create(business=self.business, name="Owner", code=RoleCode.OWNER)
        Membership.objects.create(user=self.user, business=self.business, role=role, is_active=True)
        self.supplier = Supplier.objects.create(business=self.business, name="Supplier")
        self.other_supplier = Supplier.objects.create(business=self.other_business, name="Other")
        self.ingredient = Ingredient.objects.create(
            business=self.business, name="Flour", unit=Ingredient.Unit.KG,
        )
        self.other_ingredient = Ingredient.objects.create(
            business=self.other_business, name="Other Flour", unit=Ingredient.Unit.KG,
        )
        self.order = PurchaseOrder.objects.create(
            business=self.business, supplier=self.supplier,
            order_date=date(2026, 9, 10), status=PurchaseOrder.Status.SENT,
        )
        self.order_item = PurchaseOrderItem.objects.create(
            purchase_order=self.order, ingredient=self.ingredient,
            quantity=Decimal("10.000"), unit_price=Decimal("10.00"),
        )
        self.client.force_authenticate(self.user)

    def payload(self):
        return {
            "supplier_id": self.supplier.id,
            "purchase_order_id": self.order.id,
            "invoice_number": "API-1",
            "invoice_date": "2026-09-10",
            "discount_percent": "10.00",
            "tax_percent": "20.00",
            "subtotal": "999999.99",
            "total_price": "1.00",
            "items": [{
                "ingredient_id": self.ingredient.id,
                "purchase_order_item_id": self.order_item.id,
                "purchase_order_item_id": self.order_item.id,
                "quantity": "2.000",
                "unit_price": "12.00",
                "discount_percent": "0.00",
                "tax_percent": "0.00",
            }],
        }

    def approved_invoice(self, number="POST-1", unit_price="10.00"):
        payload = self.payload()
        payload["invoice_number"] = number
        payload["items"][0]["unit_price"] = unit_price
        created = self.client.post(self.endpoint, payload, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        approved = self.client.post(
            f"{self.endpoint}{created.data['id']}/approve/", {}, format="json",
        )
        self.assertEqual(approved.status_code, status.HTTP_200_OK)
        return DjangoPurchaseInvoice.objects.get(id=created.data["id"])

    def receive(self, quantity="2.000", rejected="0.000"):
        receipt = GoodsReceipt.objects.create(
            business=self.business,
            purchase_order=self.order,
            received_by=self.user,
            received_date="2026-09-11T12:00:00Z",
        )
        GoodsReceiptItem.objects.create(
            receipt=receipt,
            purchase_order_item=self.order_item,
            received_quantity=Decimal(quantity),
            rejected_quantity=Decimal(rejected),
        )
        return receipt

    def test_create_calculates_totals_and_ignores_client_business(self):
        response = self.client.post(self.endpoint, {**self.payload(), "business_id": self.other_business.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["business_id"], self.business.id)
        self.assertEqual(response.data["status"], "draft")
        self.assertEqual(response.data["matching_status"], "not_matched")
        self.assertIsNone(response.data["approved_at"])
        self.assertIsNone(response.data["approved_by_id"])
        self.assertEqual(response.data["subtotal"], "24.00")
        self.assertEqual(response.data["discount_amount"], "2.40")
        self.assertEqual(response.data["tax_amount"], "4.32")
        self.assertEqual(response.data["total_price"], "25.92")

    def test_list_detail_and_filter_are_available(self):
        created = self.client.post(self.endpoint, self.payload(), format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        listed = self.client.get(self.endpoint, {"purchase_order_id": self.order.id})
        detail = self.client.get(f"{self.endpoint}{created.data['id']}/")
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data["id"], created.data["id"])

    def test_response_uses_raw_invoice_subtotal_and_consistent_item_values(self):
        payload = self.payload()
        payload["items"][0]["discount_percent"] = "10.00"
        payload["items"][0]["tax_percent"] = "5.00"
        response = self.client.post(self.endpoint, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["subtotal"], "24.00")
        self.assertEqual(response.data["discount_amount"], "2.40")
        self.assertEqual(response.data["tax_amount"], "3.84")
        self.assertEqual(response.data["total_price"], "24.12")
        item = response.data["items"][0]
        self.assertEqual(item["purchase_order_item_id"], self.order_item.id)
        self.assertEqual(item["subtotal"], "24.00")
        self.assertEqual(item["discount_amount"], "2.40")
        self.assertEqual(item["tax_amount"], "1.08")
        self.assertEqual(item["total_price"], "22.68")

    def test_cross_business_supplier_is_rejected(self):
        response = self.client.post(self.endpoint, {**self.payload(), "supplier_id": self.other_supplier.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_access_is_rejected(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(self.endpoint).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_rejects_client_lifecycle_fields(self):
        response = self.client.post(
            self.endpoint,
            {**self.payload(), "status": "approved", "approved_by_id": self.user.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_approve_endpoint_sets_server_controlled_metadata(self):
        created = self.client.post(self.endpoint, self.payload(), format="json")

        response = self.client.post(
            f"{self.endpoint}{created.data['id']}/approve/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "approved")
        self.assertEqual(response.data["approved_by_id"], self.user.id)
        self.assertIsNotNone(response.data["approved_at"])

    def test_approve_endpoint_rejects_second_approval(self):
        created = self.client.post(self.endpoint, self.payload(), format="json")
        approve_url = f"{self.endpoint}{created.data['id']}/approve/"
        self.assertEqual(self.client.post(approve_url, {}, format="json").status_code, status.HTTP_200_OK)

        response = self.client.post(approve_url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cross_business_approval_returns_not_found(self):
        other_order = PurchaseOrder.objects.create(
            business=self.other_business,
            supplier=self.other_supplier,
            order_date=date(2026, 9, 10),
            status=PurchaseOrder.Status.SENT,
        )
        PurchaseOrderItem.objects.create(
            purchase_order=other_order,
            ingredient=self.other_ingredient,
            quantity=Decimal("10.000"),
            unit_price=Decimal("10.00"),
        )
        other_invoice = DjangoPurchaseInvoice.objects.create(
            business=self.other_business,
            supplier=self.other_supplier,
            purchase_order=other_order,
            invoice_number="OTHER-1",
            invoice_date=date(2026, 9, 10),
            subtotal=Decimal("10.00"),
            total_price=Decimal("10.00"),
        )
        PurchaseInvoiceItem.objects.create(
            purchase_invoice=other_invoice,
            ingredient=self.other_ingredient,
            purchase_order_item=other_order.items.first(),
            purchase_order_item_id=other_order.items.first().id,
            quantity=Decimal("1.000"),
            unit_price=Decimal("10.00"),
            total_price=Decimal("10.00"),
        )

        response = self.client.post(
            f"{self.endpoint}{other_invoice.id}/approve/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_approved_invoice_cannot_be_updated(self):
        created = self.client.post(self.endpoint, self.payload(), format="json")
        self.client.post(f"{self.endpoint}{created.data['id']}/approve/", {}, format="json")

        response = self.client.put(
            f"{self.endpoint}{created.data['id']}/",
            self.payload(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_draft_and_approved_invoice_cancellation_persists_server_metadata(self):
        draft = self.client.post(self.endpoint, self.payload(), format="json")
        response = self.client.post(
            f"{self.endpoint}{draft.data['id']}/cancel/",
            {"reason": "  duplicate invoice  "}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "cancelled")
        self.assertEqual(response.data["cancellation_reason"], "duplicate invoice")
        self.assertEqual(response.data["cancelled_by_id"], self.user.id)
        self.assertIsNotNone(response.data["cancelled_at"])

        approved = self.approved_invoice("CANCEL-APPROVED")
        result = self.client.post(
            f"{self.endpoint}{approved.id}/cancel/", {"reason": "void before post"}, format="json",
        )
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data["status"], "cancelled")
        self.assertEqual(result.data["total_price"], str(approved.total_price))
        self.assertFalse(AccountsPayable.objects.filter(source_invoice_id=approved.id).exists())

    def test_cancellation_rejects_blank_unknown_and_client_controlled_fields(self):
        created = self.client.post(self.endpoint, self.payload(), format="json")
        url = f"{self.endpoint}{created.data['id']}/cancel/"
        for data in ({}, {"reason": "  "}, {"reason": "x", "status": "cancelled"},
                     {"reason": "x", "business_id": self.other_business.id},
                     {"reason": "x", "cancelled_by": self.user.id}):
            response = self.client.post(url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(DjangoPurchaseInvoice.objects.get(id=created.data["id"]).status, "draft")

    def test_cancellation_requires_authentication(self):
        created = self.client.post(self.endpoint, self.payload(), format="json")
        self.client.force_authenticate(user=None)
        response = self.client.post(
            f"{self.endpoint}{created.data['id']}/cancel/", {"reason": "unauthenticated"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cancellation_is_tenant_scoped_and_terminal(self):
        foreign = DjangoPurchaseInvoice.objects.create(
            business=self.other_business, supplier=self.other_supplier,
            purchase_order=self.order, invoice_number="FOREIGN-CANCEL", invoice_date=date(2026, 9, 10),
            subtotal=Decimal("1.00"), total_price=Decimal("1.00"),
        )
        response = self.client.post(
            f"{self.endpoint}{foreign.id}/cancel/", {"reason": "tenant check"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        created = self.client.post(self.endpoint, self.payload(), format="json")
        url = f"{self.endpoint}{created.data['id']}/cancel/"
        self.assertEqual(self.client.post(url, {"reason": "first"}, format="json").status_code, 200)
        self.assertEqual(self.client.post(url, {"reason": "second"}, format="json").status_code, 400)
        self.assertEqual(
            self.client.put(f"{self.endpoint}{created.data['id']}/", self.payload(), format="json").status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(self.client.put(url, {"reason": "x"}, format="json").status_code, 405)
        self.assertEqual(self.client.patch(url, {"reason": "x"}, format="json").status_code, 405)
        self.assertEqual(self.client.delete(url).status_code, 405)

    def test_posted_invoice_cannot_be_cancelled_and_ap_is_unchanged(self):
        invoice = self.approved_invoice("CANCEL-POSTED")
        self.receive(quantity="2.000")
        posted = self.client.post(f"{self.endpoint}{invoice.id}/post/", {}, format="json")
        self.assertEqual(posted.status_code, status.HTTP_200_OK)
        payable = AccountsPayable.objects.get(source_invoice_id=invoice.id)
        payment = SupplierPayment.objects.create(
            business=self.business, supplier=self.supplier,
            amount=Decimal("5.00"), payment_date=date(2026, 9, 12), method="cash",
        )
        allocation_response = self.client.post(
            "/api/purchase/payment-allocations/",
            {"accounts_payable_id": payable.id, "supplier_payment_id": payment.id, "amount": "1.00"},
            format="json",
        )
        self.assertEqual(allocation_response.status_code, status.HTTP_201_CREATED)
        payable.refresh_from_db()
        before = (payable.status, payable.amount, PaymentAllocation.objects.count(), payment.amount)
        result = self.client.post(
            f"{self.endpoint}{invoice.id}/cancel/", {"reason": "too late"}, format="json",
        )
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        payable.refresh_from_db()
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "posted")
        self.assertEqual(
            (payable.status, payable.amount, PaymentAllocation.objects.count(), payment.amount),
            before,
        )

    def test_draft_invoice_can_be_updated(self):
        created = self.client.post(self.endpoint, self.payload(), format="json")
        payload = {**self.payload(), "invoice_number": "API-UPDATED"}

        response = self.client.put(
            f"{self.endpoint}{created.data['id']}/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["invoice_number"], "API-UPDATED")
        self.assertEqual(response.data["status"], "draft")

    def test_get_and_list_expose_lifecycle_metadata(self):
        created = self.client.post(self.endpoint, self.payload(), format="json")

        detail = self.client.get(f"{self.endpoint}{created.data['id']}/")
        listed = self.client.get(self.endpoint)

        self.assertEqual(detail.data["status"], "draft")
        self.assertIn("approved_at", detail.data)
        self.assertIn("approved_by_id", detail.data)
        self.assertEqual(listed.data[0]["status"], "draft")

    def test_create_requires_purchase_order_item_id(self):
        payload = self.payload()
        del payload["items"][0]["purchase_order_item_id"]
        response = self.client.post(self.endpoint, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_client_cannot_control_matching_fields(self):
        for field, value in (("matching_status", "matched"), ("matched_at", "2026-10-01T00:00:00Z")):
            response = self.client.post(
                self.endpoint, {**self.payload(), field: value}, format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_rejects_po_item_from_another_order(self):
        other_order = PurchaseOrder.objects.create(
            business=self.business, supplier=self.supplier,
            order_date=date(2026, 9, 10), status=PurchaseOrder.Status.SENT,
        )
        wrong_item = PurchaseOrderItem.objects.create(
            purchase_order=other_order, ingredient=self.ingredient,
            quantity=Decimal("10"), unit_price=Decimal("10"),
        )
        payload = self.payload()
        payload["items"][0]["purchase_order_item_id"] = wrong_item.id
        response = self.client.post(self.endpoint, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_matching_endpoints_persist_and_recalculate(self):
        payload = self.payload()
        payload["items"][0]["unit_price"] = "10.00"
        created = self.client.post(self.endpoint, payload, format="json")
        invoice_id = created.data["id"]
        self.client.post(f"{self.endpoint}{invoice_id}/approve/", {}, format="json")
        match_url = f"{self.endpoint}{invoice_id}/match/"

        pending = self.client.post(match_url, {}, format="json")
        self.assertEqual(pending.status_code, status.HTTP_200_OK)
        self.assertEqual(pending.data["current"]["status"], "pending_receipt")
        self.assertEqual(pending.data["current"]["exceptions"][0]["code"], "RECEIPT_PENDING")
        self.assertEqual(pending.data["last_persisted"]["status"], "pending_receipt")
        stored = DjangoPurchaseInvoice.objects.get(id=invoice_id)
        self.assertEqual(stored.matching_status, "pending_receipt")
        self.assertIsNotNone(stored.matched_at)
        persisted_time = stored.matched_at

        receipt = GoodsReceipt.objects.create(
            business=self.business, purchase_order=self.order,
            received_by=self.user, received_date="2026-09-11T12:00:00Z",
        )
        GoodsReceiptItem.objects.create(
            receipt=receipt, purchase_order_item=self.order_item,
            received_quantity=Decimal("1.000"), rejected_quantity=Decimal("8.000"),
        )
        current = self.client.get(match_url)
        self.assertEqual(current.status_code, status.HTTP_200_OK)
        self.assertEqual(current.data["current"]["status"], "exception")
        self.assertIn("INVOICE_OVER_RECEIVED", [row["code"] for row in current.data["current"]["exceptions"]])
        self.assertEqual(current.data["last_persisted"]["status"], "pending_receipt")
        self.assertEqual(current.data["last_persisted"]["matched_at"], persisted_time.isoformat().replace("+00:00", "Z"))
        stored.refresh_from_db()
        self.assertEqual(stored.matching_status, "pending_receipt")
        self.assertEqual(stored.matched_at, persisted_time)

    def test_match_endpoint_rejects_draft_and_hides_other_tenant_invoice(self):
        created = self.client.post(self.endpoint, self.payload(), format="json")
        url = f"{self.endpoint}{created.data['id']}/match/"
        self.assertEqual(self.client.post(url, {}, format="json").status_code, status.HTTP_400_BAD_REQUEST)

        other_order = PurchaseOrder.objects.create(
            business=self.other_business, supplier=self.other_supplier,
            order_date=date(2026, 9, 10), status=PurchaseOrder.Status.SENT,
        )
        other_item = PurchaseOrderItem.objects.create(
            purchase_order=other_order, ingredient=self.other_ingredient,
            quantity=Decimal("10"), unit_price=Decimal("10"),
        )
        other_invoice = DjangoPurchaseInvoice.objects.create(
            business=self.other_business, supplier=self.other_supplier,
            purchase_order=other_order, invoice_number="OTHER-2",
            invoice_date=date(2026, 9, 10), subtotal=Decimal("10"), total_price=Decimal("10"),
            status=DjangoPurchaseInvoice.Status.APPROVED,
            approved_by=self.user, approved_at="2026-09-10T12:00:00Z",
        )
        PurchaseInvoiceItem.objects.create(
            purchase_invoice=other_invoice, ingredient=self.other_ingredient,
            purchase_order_item=other_item, quantity=Decimal("1"),
            unit_price=Decimal("10"), total_price=Decimal("10"),
        )
        self.assertEqual(
            self.client.get(f"{self.endpoint}{other_invoice.id}/match/").status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_post_creates_ap_atomically_and_uses_current_matching(self):
        invoice = self.approved_invoice("POST-CURRENT")
        pending = self.client.post(
            f"{self.endpoint}{invoice.id}/match/", {}, format="json",
        )
        self.assertEqual(pending.data["current"]["status"], "pending_receipt")
        self.assertEqual(pending.data["last_persisted"]["status"], "pending_receipt")
        # The new receipt makes the current result MATCHED despite the previously
        # persisted PENDING_RECEIPT result.
        self.receive()
        post_url = f"{self.endpoint}{invoice.id}/post/"

        response = self.client.post(post_url, {"due_date": "2026-10-30"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invoice.refresh_from_db()
        payable = AccountsPayable.objects.get(source_invoice=invoice)
        self.assertEqual(invoice.status, DjangoPurchaseInvoice.Status.POSTED)
        self.assertEqual(invoice.matching_status, "matched")
        self.assertIsNotNone(invoice.matched_at)
        self.assertIsNotNone(invoice.posted_at)
        self.assertEqual(invoice.posted_by_id, self.user.id)
        self.assertEqual(payable.business_id, invoice.business_id)
        self.assertEqual(payable.supplier_id, invoice.supplier_id)
        self.assertEqual(payable.amount, invoice.total_price)
        self.assertEqual(payable.status, AccountsPayable.Status.OPEN)
        self.assertEqual(payable.due_date.isoformat(), "2026-10-30")
        self.assertEqual(response.data["invoice"]["status"], "posted")
        self.assertEqual(response.data["accounts_payable"]["source_invoice_id"], invoice.id)

    def test_post_rejects_pending_and_exception_current_matching_results(self):
        pending = self.approved_invoice("POST-PENDING")
        response = self.client.post(f"{self.endpoint}{pending.id}/post/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(AccountsPayable.objects.filter(source_invoice=pending).exists())
        pending.refresh_from_db()
        self.assertEqual(pending.status, DjangoPurchaseInvoice.Status.APPROVED)

        exception = self.approved_invoice("POST-EXCEPTION", unit_price="12.00")
        self.receive(quantity="3.000")
        response = self.client.post(f"{self.endpoint}{exception.id}/post/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(AccountsPayable.objects.filter(source_invoice=exception).exists())

    def test_post_rejects_draft_cross_tenant_and_duplicate_commands(self):
        draft = self.client.post(self.endpoint, self.payload(), format="json")
        self.assertEqual(draft.status_code, status.HTTP_201_CREATED)
        draft_id = draft.data["id"]
        self.assertEqual(
            self.client.post(f"{self.endpoint}{draft_id}/post/", {}, format="json").status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        invoice = self.approved_invoice("POST-DUP")
        self.receive()
        url = f"{self.endpoint}{invoice.id}/post/"
        self.assertEqual(self.client.post(url, {}, format="json").status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.post(url, {}, format="json").status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(AccountsPayable.objects.filter(source_invoice=invoice).count(), 1)

        other_order = PurchaseOrder.objects.create(
            business=self.other_business, supplier=self.other_supplier,
            order_date=date(2026, 9, 10), status=PurchaseOrder.Status.SENT,
        )
        foreign = DjangoPurchaseInvoice.objects.create(
            business=self.other_business,
            supplier=self.other_supplier,
            purchase_order=other_order,
            invoice_number="POST-FOREIGN",
            invoice_date=date(2026, 9, 10),
            subtotal=Decimal("10"),
            total_price=Decimal("10"),
        )
        self.assertEqual(
            self.client.post(f"{self.endpoint}{foreign.id}/post/", {}, format="json").status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_post_rejects_client_controlled_lifecycle_and_financial_fields(self):
        invoice = self.approved_invoice("POST-PROTECTED")
        self.receive()
        protected = {
            "business_id": self.other_business.id,
            "status": "posted",
            "matching_status": "matched",
            "posted_at": "2026-10-01T00:00:00Z",
            "posted_by_id": self.user.id,
            "supplier_id": self.other_supplier.id,
            "amount": "0.01",
            "accounts_payable_status": "paid",
        }
        for field, value in protected.items():
            with self.subTest(field=field):
                response = self.client.post(
                    f"{self.endpoint}{invoice.id}/post/", {field: value}, format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(AccountsPayable.objects.filter(source_invoice=invoice).exists())

    def test_post_rolls_back_ap_and_match_state_if_invoice_persistence_fails(self):
        invoice = self.approved_invoice("POST-ROLLBACK")
        self.receive()
        with patch(
            "purchase.infrastructure.persistence.django.repositories.purchase_invoice_repository."
            "DjangoPurchaseInvoiceRepository.save_posted",
            side_effect=RuntimeError("forced invoice persistence failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "forced invoice persistence failure"):
                self.client.post(f"{self.endpoint}{invoice.id}/post/", {}, format="json")

        invoice.refresh_from_db()
        self.assertEqual(invoice.status, DjangoPurchaseInvoice.Status.APPROVED)
        self.assertEqual(invoice.matching_status, "not_matched")
        self.assertIsNone(invoice.matched_at)
        self.assertFalse(AccountsPayable.objects.filter(source_invoice=invoice).exists())

    def test_post_does_not_post_invoice_if_ap_creation_fails(self):
        invoice = self.approved_invoice("POST-AP-FAIL")
        self.receive()
        with patch(
            "purchase.infrastructure.persistence.django.repositories.accounts_payable_repository."
            "DjangoAccountsPayableRepository.create",
            side_effect=ValueError("forced AP persistence failure"),
        ):
            response = self.client.post(f"{self.endpoint}{invoice.id}/post/", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, DjangoPurchaseInvoice.Status.APPROVED)
        self.assertEqual(invoice.matching_status, "not_matched")
        self.assertFalse(AccountsPayable.objects.filter(source_invoice=invoice).exists())

    def test_posted_invoice_is_not_editable_and_post_fields_are_read_only(self):
        invoice = self.approved_invoice("POST-IMMUTABLE")
        self.receive()
        response = self.client.post(f"{self.endpoint}{invoice.id}/post/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated = self.client.put(
            f"{self.endpoint}{invoice.id}/",
            {**self.payload(), "invoice_number": "POST-CHANGED"},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_400_BAD_REQUEST)

        rejected = self.client.post(
            self.endpoint,
            {**self.payload(), "posted_at": "2026-10-07T00:00:00Z", "posted_by_id": self.user.id},
            format="json",
        )
        self.assertEqual(rejected.status_code, status.HTTP_400_BAD_REQUEST)
