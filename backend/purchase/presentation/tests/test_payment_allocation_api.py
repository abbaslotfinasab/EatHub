from datetime import date
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.enums import RoleCode
from accounts.models import Business, Membership, Role, User
from purchase.models import AccountsPayable, PaymentAllocation, PurchaseInvoice, Supplier, SupplierPayment


class PaymentAllocationAPITests(APITestCase):
    endpoint = "/api/purchase/payment-allocations/"

    def setUp(self):
        self.user = User.objects.create_user(
            email="allocation-api@example.com", password="password", name="Allocation API", number="9401",
        )
        self.business = Business.objects.create(name="Allocation API Business")
        self.other_business = Business.objects.create(name="Other Allocation API Business")
        role = Role.objects.create(business=self.business, name="Owner", code=RoleCode.OWNER)
        Membership.objects.create(user=self.user, business=self.business, role=role, is_active=True)
        self.supplier = Supplier.objects.create(business=self.business, name="Supplier")
        self.other_supplier = Supplier.objects.create(business=self.other_business, name="Other Supplier")
        self.client.force_authenticate(self.user)

    def create_payable(self, business, supplier, number, amount="100.00"):
        invoice = PurchaseInvoice.objects.create(
            business=business, supplier=supplier, invoice_number=number,
            invoice_date=date(2026, 10, 1), subtotal=Decimal(amount), total_price=Decimal(amount),
        )
        return AccountsPayable.objects.create(
            business=business, supplier=supplier, source_invoice=invoice, amount=Decimal(amount),
        )

    @staticmethod
    def create_payment(business, supplier, amount):
        return SupplierPayment.objects.create(
            business=business,
            supplier=supplier,
            amount=Decimal(amount),
            payment_date=date(2026, 10, 7),
            method="bank_transfer",
        )

    def test_create_and_read_allocation_and_ap_summary(self):
        payable = self.create_payable(self.business, self.supplier, "API-ALLOC-1")
        payment = self.create_payment(self.business, self.supplier, "60.00")

        created = self.client.post(self.endpoint, {
            "accounts_payable_id": payable.id,
            "supplier_payment_id": payment.id,
            "amount": "60.00",
        }, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.data["accounts_payable_id"], payable.id)
        self.assertEqual(created.data["supplier_payment_id"], payment.id)
        self.assertEqual(created.data["amount"], "60.00")
        self.assertEqual(created.data["business_id"], self.business.id)

        listing = self.client.get(self.endpoint)
        detail = self.client.get(f"{self.endpoint}{created.data['id']}/")
        summary = self.client.get(f"/api/purchase/accounts-payables/{payable.id}/payment-eligibility/")
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in listing.data], [created.data["id"]])
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(summary.data["status"], "partially_paid")
        self.assertTrue(summary.data["eligible"])
        self.assertEqual(summary.data["allocated_amount"], "60.00")
        self.assertEqual(summary.data["outstanding_amount"], "40.00")

    def test_list_detail_and_creation_are_tenant_scoped(self):
        own = self.create_payable(self.business, self.supplier, "API-ALLOC-OWN")
        other = self.create_payable(self.other_business, self.other_supplier, "API-ALLOC-OTHER")
        payment = self.create_payment(self.business, self.supplier, "100.00")
        own_allocation = self.client.post(self.endpoint, {
            "accounts_payable_id": own.id,
            "supplier_payment_id": payment.id,
            "amount": "10.00",
        }, format="json")
        self.assertEqual(own_allocation.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.client.get(self.endpoint).data[0]["id"], own_allocation.data["id"])
        self.assertEqual(self.client.get(f"{self.endpoint}{own_allocation.data['id']}/").status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(f"{self.endpoint}999999/").status_code, status.HTTP_404_NOT_FOUND)
        other_payment = self.create_payment(self.other_business, self.other_supplier, "10.00")
        denied = self.client.post(self.endpoint, {
            "accounts_payable_id": other.id,
            "supplier_payment_id": other_payment.id,
            "amount": "1.00",
        }, format="json")
        self.assertEqual(denied.status_code, status.HTTP_404_NOT_FOUND)

    def test_client_cannot_control_tenant_or_financial_fields(self):
        payable = self.create_payable(self.business, self.supplier, "API-ALLOC-INPUT")
        payment = self.create_payment(self.business, self.supplier, "100.00")
        response = self.client.post(self.endpoint, {
            "accounts_payable_id": payable.id,
            "supplier_payment_id": payment.id,
            "amount": "1.00",
            "business_id": self.other_business.id,
            "status": "paid",
            "allocated_amount": "100.00",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PaymentAllocation.objects.count(), 0)

    def test_balance_and_supplier_mismatches_are_rejected(self):
        payable = self.create_payable(self.business, self.supplier, "API-ALLOC-BALANCE", "10.00")
        payment = self.create_payment(self.business, self.supplier, "5.00")
        too_much = self.client.post(self.endpoint, {
            "accounts_payable_id": payable.id,
            "supplier_payment_id": payment.id,
            "amount": "6.00",
        }, format="json")
        self.assertEqual(too_much.status_code, status.HTTP_400_BAD_REQUEST)
        wrong_supplier = SupplierPayment.objects.create(
            business=self.business, supplier=self.other_supplier, amount=Decimal("10.00"),
            payment_date=date(2026, 10, 7), method="cash",
        )
        mismatch = self.client.post(self.endpoint, {
            "accounts_payable_id": payable.id,
            "supplier_payment_id": wrong_supplier.id,
            "amount": "1.00",
        }, format="json")
        self.assertEqual(mismatch.status_code, status.HTTP_400_BAD_REQUEST)

    def test_endpoints_are_read_only_except_create(self):
        payable = self.create_payable(self.business, self.supplier, "API-ALLOC-VERBS")
        payment = self.create_payment(self.business, self.supplier, "10.00")
        response = self.client.post(self.endpoint, {
            "accounts_payable_id": payable.id,
            "supplier_payment_id": payment.id,
            "amount": "1.00",
        }, format="json")
        detail = f"{self.endpoint}{response.data['id']}/"
        self.assertEqual(self.client.put(self.endpoint, {}, format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.patch(self.endpoint, {}, format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.delete(self.endpoint).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.post(detail, {}, format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.put(detail, {}, format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.patch(detail, {}, format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.delete(detail).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(self.endpoint).status_code, status.HTTP_401_UNAUTHORIZED)
