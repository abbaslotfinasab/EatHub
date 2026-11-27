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



class CustomerPresentationBoundaryTests(SimpleTestCase):
    def test_customer_presentation_does_not_import_django_models(self):
        import ast
        from pathlib import Path

        presentation = Path(__file__).parent / "presentation"
        for filename in ("views.py", "read_serializers.py"):
            syntax_tree = ast.parse(
                (presentation / filename).read_text(encoding="utf-8")
            )
            imported_modules = {
                alias.name
                for node in ast.walk(syntax_tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            }
            imported_modules.update(
                node.module
                for node in ast.walk(syntax_tree)
                if isinstance(node, ast.ImportFrom) and node.module
            )
            self.assertFalse(
                any(
                    module == "customer.models"
                    or module.startswith("django.db")
                    or module.endswith(".models")
                    for module in imported_modules
                ),
                msg=f"{filename} must not import Django ORM models",
            )

    def test_customer_read_serializer_is_not_model_serializer(self):
        from rest_framework.serializers import ModelSerializer

        self.assertFalse(issubclass(CustomerReadSerializer, ModelSerializer))


from rest_framework import status
from rest_framework.test import APITestCase

from accounts.enums import RoleCode
from accounts.models import Membership, Role, User
from accounts.views import ExplicitApplicationTenantAPIView, ExplicitTenantAPIView
from customer.presentation import views as customer_views


class CustomerTenantContextAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="customer-tenant@example.com",
            password="password",
            name="Customer Tenant",
            number="9501",
        )
        self.business = Business.objects.create(name="Customer Tenant Business")
        self.other_business = Business.objects.create(name="Other Customer Business")
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
        self.client.force_authenticate(self.user)
        self.client.credentials(HTTP_X_BUSINESS_ID=str(self.business.pk))

    def test_customer_endpoints_require_explicit_business_context(self):
        self.client.credentials()
        response = self.client.get("/api/products/customers/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "BUSINESS_CONTEXT_REQUIRED")

    def test_customer_reads_and_writes_are_scoped_to_resolved_business(self):
        created = self.client.post(
            "/api/products/customers/create",
            {"name": "Local Customer", "phone": "09121112222"},
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        customer_id = created.data["id"]

        listed = self.client.get("/api/products/customers/")
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in listed.data], [customer_id])

        self.client.credentials(HTTP_X_BUSINESS_ID=str(self.other_business.pk))
        foreign = self.client.get(f"/api/products/customers/{customer_id}/")
        self.assertEqual(foreign.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(foreign.data["code"], "BUSINESS_ACCESS_DENIED")


class CustomerTenantContextArchitectureTests(TestCase):
    def test_customer_endpoints_use_dto_only_tenant_context(self):
        endpoints = (
            customer_views.CustomerListAPIView,
            customer_views.CustomerCreateAPIView,
            customer_views.CustomerDetailAPIView,
            customer_views.CustomerUpdateAPIView,
            customer_views.CustomerDeleteAPIView,
        )
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint.__name__):
                self.assertTrue(issubclass(endpoint, ExplicitApplicationTenantAPIView))
                self.assertFalse(issubclass(endpoint, ExplicitTenantAPIView))

        import inspect

        source = inspect.getsource(customer_views)
        self.assertNotRegex(source, r"request\\.business\\b")
        self.assertNotRegex(source, r"request\\.membership\\b")
        self.assertNotRegex(source, r"request\\.role\\b")

    def test_customer_create_service_accepts_business_id_not_business_orm(self):
        import inspect

        parameters = inspect.signature(
            CustomerService.create_customer
        ).parameters
        self.assertIn("business_id", parameters)
        self.assertNotIn("business", parameters)
