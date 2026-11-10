from django.db import connection
from django.test import TestCase

from accounts.models import Business
from customer.models import Customer
from products.models import (
    Customer as LegacyCustomer,
    CustomerAccount,
    Order,
    OrderRefund,
)


class CustomerModelOwnershipTests(TestCase):
    def test_customer_uses_existing_products_table_and_legacy_import(self):
        self.assertEqual(Customer._meta.label, "customer.Customer")
        self.assertEqual(Customer._meta.db_table, "products_customer")
        self.assertIs(LegacyCustomer, Customer)
        self.assertIs(Order._meta.get_field("customer").remote_field.model, Customer)
        self.assertIs(CustomerAccount._meta.get_field("customer").remote_field.model, Customer)
        self.assertIs(OrderRefund._meta.get_field("customer").remote_field.model, Customer)

        business = Business.objects.create(name="Customer Model Ownership")
        customer = Customer.objects.create(
            business=business,
            name="Existing Table Customer",
            phone="09120000000",
        )

        with connection.cursor() as cursor:
            tables = connection.introspection.table_names(cursor)

        self.assertIn("products_customer", tables)
        self.assertEqual(
            LegacyCustomer.objects.get(pk=customer.pk).phone,
            "09120000000",
        )


from django.test import SimpleTestCase

from customer.presentation.read_serializers import (
    CustomerDetailReadSerializer,
    CustomerReadSerializer,
)
from products.serializers.customer_serializer import (
    CustomerDetailSerializer,
    CustomerSerializer,
)


class CustomerReadSerializerOwnershipTests(SimpleTestCase):
    def test_customer_module_owns_read_serializers(self):
        self.assertEqual(CustomerReadSerializer.__module__, "customer.presentation.read_serializers")
        self.assertEqual(
            CustomerDetailReadSerializer.__module__,
            "customer.presentation.read_serializers",
        )

    def test_products_namespace_keeps_backward_compatible_aliases(self):
        self.assertIs(CustomerSerializer, CustomerReadSerializer)
        self.assertIs(CustomerDetailSerializer, CustomerDetailReadSerializer)
