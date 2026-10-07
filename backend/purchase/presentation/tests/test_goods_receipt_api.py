from datetime import date, datetime
from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.enums import RoleCode
from accounts.models import Business, Membership, Role, User
from inventory.models import Ingredient, StockTransaction, Warehouse
from purchase.models import (
    GoodsReceipt as DjangoGoodsReceipt,
    PurchaseOrder as DjangoPurchaseOrder,
    PurchaseOrderItem as DjangoPurchaseOrderItem,
    Supplier as DjangoSupplier,
)


class GoodsReceiptAPITests(APITestCase):
    endpoint = "/api/purchase/goods-receipts/"

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="receiver@example.com",
            password="password",
            name="Receiver",
            number="7001",
        )
        self.other_user = User.objects.create_user(
            email="other-receiver@example.com",
            password="password",
            name="Other Receiver",
            number="7002",
        )
        self.business = Business.objects.create(name="Goods Receipt Business")
        self.other_business = Business.objects.create(
            name="Other Goods Receipt Business"
        )
        role = Role.objects.create(
            business=self.business,
            name="Owner",
            code=RoleCode.OWNER,
        )
        other_role = Role.objects.create(
            business=self.other_business,
            name="Owner",
            code=RoleCode.OWNER,
        )
        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=role,
            is_active=True,
        )
        Membership.objects.create(
            user=self.other_user,
            business=self.other_business,
            role=other_role,
            is_active=True,
        )
        self.supplier = DjangoSupplier.objects.create(
            business=self.business,
            name="Supplier",
        )
        self.other_supplier = DjangoSupplier.objects.create(
            business=self.other_business,
            name="Other Supplier",
        )
        self.ingredient = Ingredient.objects.create(
            business=self.business,
            name="Flour",
            unit=Ingredient.Unit.KG,
        )
        self.other_ingredient = Ingredient.objects.create(
            business=self.other_business,
            name="Other Flour",
            unit=Ingredient.Unit.KG,
        )
        Warehouse.objects.create(
            business=self.business,
            name="Main",
            is_default=True,
        )
        Warehouse.objects.create(
            business=self.other_business,
            name="Other Main",
            is_default=True,
        )
        self.order = self.create_order(self.business, self.supplier, self.ingredient)
        self.other_order = self.create_order(
            self.other_business,
            self.other_supplier,
            self.other_ingredient,
        )
        self.client.force_authenticate(self.user)

    @staticmethod
    def create_order(business, supplier, ingredient, status="sent"):
        order = DjangoPurchaseOrder.objects.create(
            business=business,
            supplier=supplier,
            order_date=date(2026, 9, 8),
            status=status,
        )
        item = DjangoPurchaseOrderItem.objects.create(
            purchase_order=order,
            ingredient=ingredient,
            quantity=Decimal("10"),
            unit_price=Decimal("500.00"),
        )
        return order, item

    def detail_endpoint(self, receipt_id: int) -> str:
        return f"{self.endpoint}{receipt_id}/"

    def payload(self, **overrides: object) -> dict:
        payload = {
            "purchase_order_id": self.order[0].id,
            "received_date": "2026-09-08T12:00:00Z",
            "notes": "Received shipment",
            "items": [
                {
                    "purchase_order_item_id": self.order[1].id,
                    "received_quantity": "4.000",
                    "rejected_quantity": "0.000",
                }
            ],
        }
        payload.update(overrides)
        return payload

    def create_receipt(self, **overrides):
        return self.client.post(
            self.endpoint,
            self.payload(**overrides),
            format="json",
        )

    def test_create_uses_current_business_and_authenticated_user(self):
        response = self.create_receipt(
            business_id=self.other_business.id,
            received_by_id=self.other_user.id,
            status="received",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["business_id"], self.business.id)
        self.assertEqual(response.data["received_by_id"], self.user.id)

    def test_list_and_detail_are_available(self):
        created = self.create_receipt()
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        listed = self.client.get(self.endpoint)
        detail = self.client.get(self.detail_endpoint(created.data["id"]))

        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data["id"], created.data["id"])

    def test_cross_business_detail_returns_not_found(self):
        other_receipt = DjangoGoodsReceipt.objects.create(
            business=self.other_business,
            purchase_order=self.other_order[0],
            received_by=self.other_user,
            received_date=datetime(2026, 9, 8, 12),
        )

        response = self.client.get(self.detail_endpoint(other_receipt.id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_query_business_id_cannot_override_tenant(self):
        created = self.create_receipt()

        response = self.client.get(
            self.endpoint,
            {"business_id": self.other_business.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [created.data["id"]])

    def test_unauthenticated_access_is_rejected(self):
        self.client.force_authenticate(user=None)

        self.assertEqual(
            self.client.post(self.endpoint, self.payload(), format="json").status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(
            self.client.get(self.endpoint).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_unauthenticated_detail_is_rejected(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.detail_endpoint(1))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_purchase_order_status_is_bad_request(self):
        self.order[0].status = DjangoPurchaseOrder.Status.DRAFT
        self.order[0].save(update_fields=["status", "updated_at"])

        response = self.create_receipt()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_foreign_purchase_order_is_not_found(self):
        response = self.create_receipt(purchase_order_id=self.other_order[0].id)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_foreign_purchase_order_line_is_bad_request(self):
        response = self.create_receipt(items=[{
            "purchase_order_item_id": self.other_order[1].id,
            "received_quantity": "1.000",
            "rejected_quantity": "0.000",
        }])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_and_duplicate_lines_are_bad_request(self):
        invalid = self.create_receipt(items=[{
            "purchase_order_item_id": 999999,
            "received_quantity": "1.000",
            "rejected_quantity": "0.000",
        }])
        duplicate = self.create_receipt(items=[
            self.payload()["items"][0],
            self.payload()["items"][0],
        ])

        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)

    def test_over_receiving_is_bad_request(self):
        response = self.create_receipt(items=[{
            "purchase_order_item_id": self.order[1].id,
            "received_quantity": "11.000",
            "rejected_quantity": "0.000",
        }])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_full_receipt_updates_order_to_received(self):
        response = self.create_receipt(items=[{
            "purchase_order_item_id": self.order[1].id,
            "received_quantity": "10.000",
            "rejected_quantity": "0.000",
        }])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.order[0].refresh_from_db()
        self.assertEqual(self.order[0].status, DjangoPurchaseOrder.Status.RECEIVED)

    def test_other_business_receipts_are_hidden_from_list(self):
        other_receipt = DjangoGoodsReceipt.objects.create(
            business=self.other_business,
            purchase_order=self.other_order[0],
            received_by=self.other_user,
            received_date=datetime(2026, 9, 8, 12),
        )
        created = self.create_receipt()

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [created.data["id"]])
        self.assertNotIn(other_receipt.id, [item["id"] for item in response.data])

    def test_invalid_received_date_is_bad_request(self):
        response = self.create_receipt(received_date="not-a-date")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_items_are_bad_request(self):
        response = self.create_receipt(items=[])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_and_patch_are_not_supported(self):
        self.assertEqual(
            self.client.put(self.endpoint, self.payload(), format="json").status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(
            self.client.patch(self.endpoint, self.payload(), format="json").status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        created = self.create_receipt()
        self.assertEqual(
            self.client.delete(f"{self.endpoint}{created.data['id']}/").status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_stock_details_are_not_exposed(self):
        response = self.create_receipt()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("stock_transaction_id", response.data)
        self.assertNotIn("warehouse_id", response.data)
        self.assertNotIn("stock_quantity", response.data)

    def test_received_by_filter_remains_business_scoped(self):
        created = self.create_receipt()

        response = self.client.get(
            self.endpoint,
            {"received_by_id": self.other_user.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
        self.assertNotEqual(response.data, [created.data])

    def test_partial_receipt_updates_order_and_creates_stock_for_received_only(self):
        response = self.create_receipt(items=[{
            "purchase_order_item_id": self.order[1].id,
            "received_quantity": "4.000",
            "rejected_quantity": "3.000",
        }])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.order[0].refresh_from_db()
        self.assertEqual(self.order[0].status, DjangoPurchaseOrder.Status.PARTIAL)
        self.assertEqual(StockTransaction.objects.get().quantity, Decimal("4"))

    def test_list_filters_are_scoped_and_forwarded(self):
        created = self.create_receipt()

        response = self.client.get(
            self.endpoint,
            {
                "purchase_order_id": self.order[0].id,
                "received_by_id": self.user.id,
                "received_from": "2026-09-08T00:00:00Z",
                "received_to": "2026-09-09T00:00:00Z",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [created.data["id"]])
