from datetime import date
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.enums import RoleCode
from accounts.models import Business, Membership, Role, User
from purchase.models import AccountsPayable, PurchaseInvoice, Supplier


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
