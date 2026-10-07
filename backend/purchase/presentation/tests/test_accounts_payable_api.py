from datetime import date
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.enums import RoleCode
from accounts.models import Business, Membership, Role, User
from purchase.models import (
    AccountsPayable,
    PaymentAllocation,
    PurchaseInvoice,
    Supplier,
    SupplierPayment,
)


class AccountsPayableAPITests(APITestCase):
    endpoint = "/api/purchase/accounts-payables/"

    def eligibility_url(self, payable_id):
        return f"{self.endpoint}{payable_id}/payment-eligibility/"

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
        self.client.force_authenticate(self.user)

    def create_payable(self, business, supplier, invoice_number):
        invoice = PurchaseInvoice.objects.create(
            business=business,
            supplier=supplier,
            invoice_number=invoice_number,
            invoice_date=date(2026, 10, 1),
            subtotal=Decimal("10.00"),
            total_price=Decimal("10.00"),
        )
        return AccountsPayable.objects.create(
            business=business,
            supplier=supplier,
            source_invoice=invoice,
            amount=Decimal("10.00"),
        )

    def test_list_and_detail_are_scoped_to_active_business(self):
        payable = self.create_payable(self.business, self.supplier, "AP-LIST")
        other = self.create_payable(self.other_business, self.other_supplier, "AP-OTHER")

        listing = self.client.get(self.endpoint)
        detail = self.client.get(f"{self.endpoint}{payable.id}/")
        other_detail = self.client.get(f"{self.endpoint}{other.id}/")

        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in listing.data], [payable.id])
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(other_detail.status_code, status.HTTP_404_NOT_FOUND)

    def test_accounts_payable_cannot_be_created_outside_invoice_posting(self):
        response = self.client.post(self.endpoint, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_payment_eligibility_is_read_only_for_every_ap_status(self):
        cases = (
            (AccountsPayable.Status.OPEN, Decimal("0.00"), "open", True, None),
            (AccountsPayable.Status.PARTIALLY_PAID, Decimal("2.50"), "partially_paid", True, None),
            (AccountsPayable.Status.PAID, Decimal("10.00"), "paid", False, "already_paid"),
            (AccountsPayable.Status.CANCELLED, Decimal("0.00"), "cancelled", False, "cancelled"),
        )
        for index, (persisted_status, allocated, expected_status, eligible, reason) in enumerate(cases):
            with self.subTest(status=persisted_status):
                payable = self.create_payable(
                    self.business,
                    self.supplier,
                    f"AP-ELIGIBILITY-{index}",
                )
                AccountsPayable.objects.filter(id=payable.id).update(status=persisted_status)
                if allocated:
                    payment = SupplierPayment.objects.create(
                        business=self.business,
                        supplier=self.supplier,
                        amount=allocated,
                        payment_date=date(2026, 10, 7),
                        method="cash",
                    )
                    PaymentAllocation.objects.create(
                        business=self.business,
                        accounts_payable=payable,
                        payment=payment,
                        invoice=payable.source_invoice,
                        amount=allocated,
                        allocated_at=payable.created_at,
                    )
                payments_before = SupplierPayment.objects.count()
                allocations_before = PaymentAllocation.objects.count()

                response = self.client.get(self.eligibility_url(payable.id))

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["accounts_payable_id"], payable.id)
                self.assertEqual(response.data["eligible"], eligible)
                self.assertEqual(response.data["status"], expected_status)
                self.assertEqual(response.data["amount"], "10.00")
                self.assertEqual(response.data["reason"], reason)
                self.assertEqual(response.data["allocated_amount"], f"{allocated:.2f}")
                self.assertEqual(response.data["outstanding_amount"], f"{Decimal('10.00') - allocated:.2f}")
                payable.refresh_from_db()
                self.assertEqual(payable.status, persisted_status)
                self.assertEqual(SupplierPayment.objects.count(), payments_before)
                self.assertEqual(PaymentAllocation.objects.count(), allocations_before)

    def test_payment_eligibility_hides_other_business_and_missing_payables(self):
        own = self.create_payable(self.business, self.supplier, "AP-ELIGIBILITY-OWN")
        other = self.create_payable(self.other_business, self.other_supplier, "AP-ELIGIBILITY-OTHER")

        own_response = self.client.get(
            self.eligibility_url(own.id),
            {"business_id": self.other_business.id},
        )
        self.assertEqual(own_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.get(self.eligibility_url(other.id)).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.get(self.eligibility_url(999999)).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_payment_eligibility_requires_authentication(self):
        payable = self.create_payable(self.business, self.supplier, "AP-ELIGIBILITY-UNAUTH")
        self.client.force_authenticate(user=None)

        response = self.client.get(self.eligibility_url(payable.id))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_payment_eligibility_endpoint_is_get_only(self):
        payable = self.create_payable(self.business, self.supplier, "AP-ELIGIBILITY-READONLY")
        url = self.eligibility_url(payable.id)

        self.assertEqual(self.client.post(url, {}, format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.put(url, {}, format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.patch(url, {}, format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
