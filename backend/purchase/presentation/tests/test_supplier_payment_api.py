from datetime import date
from decimal import Decimal
from uuid import uuid4

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.enums import RoleCode
from accounts.models import Business, Membership, Role, RolePermission, User
from accounts.services.rbac_initializer import RBACInitializer
from core.enums import PermissionCode
from purchase.models import (
    AccountsPayable,
    PaymentAllocation,
    PurchaseInvoice,
    Supplier,
    SupplierPayment as DjangoSupplierPayment,
)


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
            is_system=True,
        )
        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=role,
            is_active=True,
        )
        RBACInitializer.initialize(self.business)
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
            "idempotency_key": str(uuid4()),
            "amount": "100000000.00",
            "payment_date": "2026-09-19",
            "method": "bank_transfer",
        }
        payload.update(overrides)
        return payload

    def create_payment(self, amount, supplier=None, business=None):
        return DjangoSupplierPayment.objects.create(
            business=business or self.business,
            supplier=supplier or self.supplier,
            amount=Decimal(amount),
            payment_date=date(2026, 9, 19),
            method="bank_transfer",
        )

    def create_payable(self, business, supplier, invoice_number, amount="200.00"):
        invoice = PurchaseInvoice.objects.create(
            business=business,
            supplier=supplier,
            invoice_number=invoice_number,
            invoice_date=date(2026, 9, 1),
            subtotal=Decimal(amount),
            total_price=Decimal(amount),
        )
        return AccountsPayable.objects.create(
            business=business,
            supplier=supplier,
            source_invoice=invoice,
            amount=Decimal(amount),
        )

    def create_allocation(self, payment, amount, business=None, payable=None):
        business = business or self.business
        payable = payable or self.create_payable(
            business,
            self.supplier if business == self.business else self.other_supplier,
            f"PAYMENT-READ-{uuid4()}",
        )
        return PaymentAllocation.objects.create(
            business=business,
            accounts_payable=payable,
            payment=payment,
            invoice=payable.source_invoice,
            amount=Decimal(amount),
            allocated_at=payment.created_at,
        )

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

    def test_supplier_payment_list_returns_zero_partial_and_full_allocation_balances(self):
        unallocated = self.create_payment("100.00")
        partial = self.create_payment("80.00")
        fully_allocated = self.create_payment("50.00")

        self.create_allocation(partial, "25.50")
        self.create_allocation(fully_allocated, "50.00")

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rows = {row["id"]: row for row in response.data}
        self.assertEqual(rows[unallocated.id]["allocated_amount"], "0.00")
        self.assertEqual(rows[unallocated.id]["remaining_amount"], "100.00")
        self.assertEqual(rows[partial.id]["allocated_amount"], "25.50")
        self.assertEqual(rows[partial.id]["remaining_amount"], "54.50")
        self.assertEqual(rows[fully_allocated.id]["allocated_amount"], "50.00")
        self.assertEqual(rows[fully_allocated.id]["remaining_amount"], "0.00")

    def test_supplier_payment_allocation_balance_aggregation_is_business_scoped(self):
        payment = self.create_payment("100.00")
        foreign_payable = self.create_payable(
            self.other_business,
            self.other_supplier,
            "FOREIGN-ALLOCATION-READ-MODEL",
            "100.00",
        )
        # A deliberately inconsistent legacy row verifies that a foreign
        # business allocation is never included in this tenant's payment balance.
        self.create_allocation(
            payment,
            "40.00",
            business=self.other_business,
            payable=foreign_payable,
        )

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        row = next(item for item in response.data if item["id"] == payment.id)
        self.assertEqual(row["allocated_amount"], "0.00")
        self.assertEqual(row["remaining_amount"], "100.00")

    def test_supplier_payment_balance_fields_preserve_existing_filters(self):
        included = self.create_payment("100.00")
        excluded = self.create_payment("200.00", supplier=self.other_supplier, business=self.other_business)

        response = self.client.get(self.endpoint, {"supplier_id": self.supplier.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in response.data], [included.id])
        self.assertEqual(response.data[0]["allocated_amount"], "0.00")
        self.assertEqual(response.data[0]["remaining_amount"], "100.00")
        self.assertNotIn(excluded.id, [row["id"] for row in response.data])

    def test_retry_with_same_key_replays_payment(self):
        key = str(uuid4())
        payload = self.payload(idempotency_key=key)
        first = self.client.post(self.endpoint, payload, format="json")
        retry = self.client.post(self.endpoint, payload, format="json")

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(retry.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data["id"], retry.data["id"])
        self.assertEqual(DjangoSupplierPayment.objects.count(), 1)

    def test_same_key_with_different_payload_is_rejected(self):
        key = str(uuid4())
        first = self.client.post(
            self.endpoint,
            self.payload(idempotency_key=key),
            format="json",
        )
        retry = self.client.post(
            self.endpoint,
            self.payload(idempotency_key=key, amount="90.00"),
            format="json",
        )

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(retry.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(DjangoSupplierPayment.objects.count(), 1)

    def test_creation_requires_idempotency_key(self):
        payload = self.payload()
        payload.pop("idempotency_key")
        response = self.client.post(self.endpoint, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(DjangoSupplierPayment.objects.count(), 0)

    def test_supplier_payment_detail_is_read_only(self):
        created = self.client.post(self.endpoint, self.payload(), format="json")
        url = f"{self.endpoint}{created.data['id']}/"
        self.assertEqual(self.client.put(url, self.payload(), format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.patch(url, self.payload(), format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_customer_payment_permission_does_not_authorize_supplier_payment(self):
        accountant_role = Role.objects.get(
            business=self.business,
            code="ACCOUNTANT",
        )
        self.assertTrue(
            RolePermission.objects.filter(
                role=accountant_role,
                permission__code=PermissionCode.PAYMENTS_MANAGE.value,
            ).exists()
        )
        self.assertFalse(
            RolePermission.objects.filter(
                role=accountant_role,
                permission__code=PermissionCode.PURCHASE_PAYMENT_CREATE.value,
            ).exists()
        )
        accountant = User.objects.create_user(
            email="customer-payment-only@example.com",
            password="password",
            name="Customer Payment Only",
            number="9202",
        )
        Membership.objects.create(
            user=accountant,
            business=self.business,
            role=accountant_role,
            is_active=True,
        )
        self.client.force_authenticate(accountant)

        response = self.client.post(self.endpoint, self.payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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
