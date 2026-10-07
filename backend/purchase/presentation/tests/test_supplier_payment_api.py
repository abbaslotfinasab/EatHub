from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.enums import RoleCode
from accounts.models import Business, Membership, Role, User
from purchase.models import Supplier, SupplierPayment as DjangoSupplierPayment


class SupplierPaymentAPITests(APITestCase):
    endpoint = "/api/purchase/supplier-payments/"

    def setUp(self):
        self.user = User.objects.create_user(
            email="payment@example.com",
            password="password",
            name="Payment User",
            number="9201",
        )
        self.business = Business.objects.create(name="Payment API Business")
        self.other_business = Business.objects.create(name="Other API Business")
        role = Role.objects.create(
            business=self.business,
            name="Owner",
            code=RoleCode.OWNER,
        )
        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=role,
            is_active=True,
        )
        self.supplier = Supplier.objects.create(
            business=self.business,
            name="Supplier",
        )
        self.other_supplier = Supplier.objects.create(
            business=self.other_business,
            name="Other Supplier",
        )
        self.client.force_authenticate(self.user)

    def payload(self, **overrides):
        payload = {
            "supplier_id": self.supplier.id,
            "amount": "100000000.00",
            "payment_date": "2026-09-19",
            "method": "bank_transfer",
        }
        payload.update(overrides)
        return payload

    def test_create_get_and_list_payment_without_invoice(self):
        created = self.client.post(self.endpoint, self.payload(), format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.data["business_id"], self.business.id)
        self.assertEqual(created.data["amount"], "100000000.00")
        self.assertIsNone(
            DjangoSupplierPayment.objects.get(id=created.data["id"]).invoice_id
        )

        detail = self.client.get(f"{self.endpoint}{created.data['id']}/")
        listed = self.client.get(self.endpoint)
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(listed.data[0]["id"], created.data["id"])

    def test_supplier_payment_detail_is_read_only(self):
        created = self.client.post(self.endpoint, self.payload(), format="json")
        url = f"{self.endpoint}{created.data['id']}/"
        self.assertEqual(self.client.put(url, self.payload(), format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.patch(url, self.payload(), format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_client_business_is_ignored_and_invoice_id_is_rejected(self):
        ignored = self.client.post(
            self.endpoint,
            self.payload(business_id=self.other_business.id),
            format="json",
        )
        self.assertEqual(ignored.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ignored.data["business_id"], self.business.id)

        rejected = self.client.post(
            self.endpoint,
            self.payload(invoice_id=1),
            format="json",
        )
        self.assertEqual(rejected.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(DjangoSupplierPayment.objects.count(), 1)

    def test_invalid_amount_and_method_are_rejected(self):
        self.assertEqual(
            self.client.post(
                self.endpoint,
                self.payload(amount="0.00"),
                format="json",
            ).status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            self.client.post(
                self.endpoint,
                self.payload(method="invalid"),
                format="json",
            ).status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_cross_business_supplier_and_payment_are_isolated(self):
        foreign_payment = DjangoSupplierPayment.objects.create(
            business=self.other_business,
            supplier=self.other_supplier,
            amount=Decimal("10.00"),
            payment_date=date(2026, 9, 19),
            method="cash",
        )
        foreign_supplier = self.client.post(
            self.endpoint,
            self.payload(supplier_id=self.other_supplier.id),
            format="json",
        )
        self.assertEqual(foreign_supplier.status_code, status.HTTP_404_NOT_FOUND)
        detail = self.client.get(f"{self.endpoint}{foreign_payment.id}/")
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)
