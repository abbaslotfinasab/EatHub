from django.test import TestCase

# Create your tests here.

from django.test import SimpleTestCase

from financial.models import CustomerAccount, CustomerTransaction, OrderRefund
from products.models import (
    CustomerAccount as LegacyCustomerAccount,
    CustomerTransaction as LegacyCustomerTransaction,
    OrderRefund as LegacyOrderRefund,
)


class FinancialModelOwnershipTests(SimpleTestCase):
    def test_financial_models_keep_existing_physical_tables(self):
        self.assertEqual(CustomerAccount._meta.db_table, "products_customeraccount")
        self.assertEqual(CustomerTransaction._meta.db_table, "products_customertransaction")
        self.assertEqual(OrderRefund._meta.db_table, "products_orderrefund")

    def test_financial_models_are_owned_by_financial_app(self):
        self.assertEqual(CustomerAccount._meta.app_label, "financial")
        self.assertEqual(CustomerTransaction._meta.app_label, "financial")
        self.assertEqual(OrderRefund._meta.app_label, "financial")

    def test_legacy_imports_resolve_to_financial_models(self):
        self.assertIs(LegacyCustomerAccount, CustomerAccount)
        self.assertIs(LegacyCustomerTransaction, CustomerTransaction)
        self.assertIs(LegacyOrderRefund, OrderRefund)

    def test_cross_module_relations_point_to_their_owning_models(self):
        self.assertEqual(
            CustomerAccount._meta.get_field("customer").remote_field.model._meta.label_lower,
            "customer.customer",
        )
        self.assertEqual(
            CustomerTransaction._meta.get_field("order").remote_field.model._meta.label_lower,
            "products.order",
        )
        self.assertEqual(
            CustomerTransaction._meta.get_field("account").remote_field.model._meta.label_lower,
            "financial.customeraccount",
        )
        self.assertEqual(
            OrderRefund._meta.get_field("customer").remote_field.model._meta.label_lower,
            "customer.customer",
        )


from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Permission, Role, User
from accounts.services.rbac_initializer import RBACInitializer
from core.enums import PermissionCode
from customer.models import Customer


class FinancialWalletApiTenantContextTests(APITestCase):
    def setUp(self):
        for permission_code in PermissionCode:
            Permission.objects.get_or_create(
                code=permission_code.value,
                defaults={"name": permission_code.label},
            )
        self.business = Business.objects.create(name="Financial API Tenant")
        self.foreign_business = Business.objects.create(name="Foreign Financial Tenant")
        RBACInitializer.initialize(self.business)
        RBACInitializer.initialize(self.foreign_business)
        owner_role = Role.objects.get(business=self.business, code="OWNER")
        self.user = User.objects.create_user(
            email="financial-api-owner@example.test",
            password="test-password",
            name="Financial API Owner",
            number="95001",
        )
        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=owner_role,
            is_active=True,
        )
        self.customer = Customer.objects.create(
            business=self.business,
            name="Local Financial Customer",
            phone="95001",
        )
        self.foreign_customer = Customer.objects.create(
            business=self.foreign_business,
            name="Foreign Financial Customer",
            phone="95002",
        )
        self.account = CustomerAccount.objects.create(
            business=self.business,
            customer=self.customer,
            balance=Decimal("20.00"),
            ledger_opening_balance=Decimal("20.00"),
            ledger_opening_balance_verified=True,
        )
        self.client.force_authenticate(self.user)
        self.client.defaults["HTTP_X_BUSINESS_ID"] = str(self.business.id)

    def test_wallet_read_endpoints_require_explicit_business_context(self):
        self.client.defaults.pop("HTTP_X_BUSINESS_ID", None)
        for path in (
            f"/api/products/customers/{self.customer.id}/account/",
            f"/api/products/customers/{self.customer.id}/transactions/",
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(response.data["code"], "BUSINESS_CONTEXT_REQUIRED")

    def test_wallet_write_endpoints_require_explicit_business_context(self):
        self.client.defaults.pop("HTTP_X_BUSINESS_ID", None)
        for action in ("credit", "debit", "adjust"):
            with self.subTest(action=action):
                response = self.client.post(
                    f"/api/products/customers/{self.customer.id}/{action}/",
                    {"amount": "5.00", "description": "tenant context test"},
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(response.data["code"], "BUSINESS_CONTEXT_REQUIRED")

    def test_wallet_endpoints_reject_business_without_membership(self):
        self.client.defaults["HTTP_X_BUSINESS_ID"] = str(self.foreign_business.id)
        response = self.client.get(
            f"/api/products/customers/{self.customer.id}/account/"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["code"], "BUSINESS_ACCESS_DENIED")

    def test_wallet_reads_cannot_cross_customer_business_boundary(self):
        response = self.client.get(
            f"/api/products/customers/{self.foreign_customer.id}/account/"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_wallet_urls_preserve_account_and_transaction_response_contracts(self):
        account_response = self.client.get(
            f"/api/products/customers/{self.customer.id}/account/"
        )
        transaction_response = self.client.get(
            f"/api/products/customers/{self.customer.id}/transactions/"
        )
        self.assertEqual(account_response.status_code, status.HTTP_200_OK)
        self.assertEqual(account_response.data["id"], self.account.id)
        self.assertEqual(account_response.data["balance"], "20.00")
        self.assertEqual(transaction_response.status_code, status.HTTP_200_OK)
        self.assertEqual(transaction_response.data, [])

    def test_wallet_credit_endpoint_keeps_financial_authorization_and_ledger(self):
        response = self.client.post(
            f"/api/products/customers/{self.customer.id}/credit/",
            {"amount": "5.00", "description": "Top up"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("25.00"))
        self.assertEqual(
            CustomerTransaction.objects.filter(
                account=self.account,
                type=CustomerTransaction.Type.CREDIT,
            ).count(),
            1,
        )
