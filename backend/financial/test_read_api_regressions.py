from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Permission, Role, User
from accounts.services.rbac_initializer import RBACInitializer
from core.enums import PermissionCode
from customer.models import Customer
from financial.models import CustomerAccount


class FinancialWalletReadRegressionTests(APITestCase):
    def setUp(self):
        for permission_code in PermissionCode:
            Permission.objects.get_or_create(
                code=permission_code.value,
                defaults={"name": permission_code.label},
            )
        self.business = Business.objects.create(name="Wallet Read Tenant")
        self.foreign_business = Business.objects.create(name="Foreign Wallet Tenant")
        RBACInitializer.initialize(self.business)
        RBACInitializer.initialize(self.foreign_business)
        role = Role.objects.get(business=self.business, code="OWNER")
        self.user = User.objects.create_user(
            email="wallet-read-owner@example.test",
            password="test-password",
            name="Wallet Read Owner",
            number="96001",
        )
        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=role,
            is_active=True,
        )
        self.customer_without_account = Customer.objects.create(
            business=self.business,
            name="No Wallet Account",
            phone="96002",
        )
        self.foreign_customer = Customer.objects.create(
            business=self.foreign_business,
            name="Foreign Wallet Customer",
            phone="96003",
        )
        self.client.force_authenticate(self.user)
        self.client.defaults["HTTP_X_BUSINESS_ID"] = str(self.business.id)

    def test_account_and_transaction_reads_return_404_without_an_account(self):
        for suffix in ("account", "transactions"):
            with self.subTest(suffix=suffix):
                response = self.client.get(
                    f"/api/products/customers/{self.customer_without_account.id}/{suffix}/"
                )
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_wallet_mutations_cannot_target_a_foreign_business_customer(self):
        for action in ("credit", "debit", "adjust"):
            with self.subTest(action=action):
                response = self.client.post(
                    f"/api/products/customers/{self.foreign_customer.id}/{action}/",
                    {"amount": "5.00", "description": "cross-tenant regression"},
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(
            CustomerAccount.objects.filter(customer=self.foreign_customer).exists()
        )
