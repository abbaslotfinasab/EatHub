from datetime import date
from decimal import Decimal

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
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
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
