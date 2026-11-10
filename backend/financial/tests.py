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
