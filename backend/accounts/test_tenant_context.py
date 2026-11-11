from django.test import TestCase

from accounts.models import Business, Membership, User
from accounts.services.business_service import BusinessService
from accounts.tenant_context import (
    BusinessAccessDenied,
    BusinessContextRequired,
    resolve_tenant_context,
)


class TenantContextResolverTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="tenant-context@example.test",
            password="test-password",
            name="Tenant Context User",
            number="tenant-context-user",
        )
        self.business = BusinessService.create_business(self.user, "Tenant Context Cafe")

    def test_explicit_membership_resolves_business_role_and_permissions(self):
        context = resolve_tenant_context(
            user=self.user,
            business_id=str(self.business.pk),
        )
        membership = Membership.objects.get(user=self.user, business=self.business)
        self.assertEqual(context.user_id, self.user.pk)
        self.assertEqual(context.business_id, self.business.pk)
        self.assertEqual(context.membership_id, membership.pk)
        self.assertEqual(context.role_id, membership.role_id)
        self.assertIn("orders.view", context.permissions)
        self.assertEqual(context.business.pk, membership.business_id)
        self.assertEqual(context.membership.pk, membership.pk)

    def test_missing_business_context_fails_closed(self):
        with self.assertRaises(BusinessContextRequired) as error:
            resolve_tenant_context(user=self.user, business_id=None)
        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(error.exception.detail["code"], "BUSINESS_CONTEXT_REQUIRED")

    def test_membership_for_another_business_is_denied(self):
        other_business = Business.objects.create(name="Other Tenant Cafe")
        with self.assertRaises(BusinessAccessDenied):
            resolve_tenant_context(user=self.user, business_id=other_business.pk)

    def test_inactive_membership_is_denied(self):
        Membership.objects.filter(user=self.user, business=self.business).update(is_active=False)
        with self.assertRaises(BusinessAccessDenied):
            resolve_tenant_context(user=self.user, business_id=self.business.pk)

    def test_inactive_business_is_denied(self):
        Business.objects.filter(pk=self.business.pk).update(is_active=False)
        with self.assertRaises(BusinessAccessDenied):
            resolve_tenant_context(user=self.user, business_id=self.business.pk)



class TenantAPIViewContextTests(TestCase):
    def setUp(self):
        from rest_framework.test import APIClient

        self.client = APIClient()
        self.user = User.objects.create_user(
            email="tenant-api@example.test",
            password="test-password",
            name="Tenant API User",
            number="tenant-api-user",
        )
        self.business = BusinessService.create_business(self.user, "Tenant API Cafe")
        self.client.force_authenticate(user=self.user)
        self.url = "/api/accounts/business/inventory-settings/"

    def test_business_scoped_api_requires_explicit_context(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "BUSINESS_CONTEXT_REQUIRED")

    def test_business_scoped_api_rejects_unowned_business_context(self):
        other_business = Business.objects.create(name="Unowned Cafe")
        self.client.credentials(HTTP_X_BUSINESS_ID=str(other_business.pk))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "BUSINESS_ACCESS_DENIED")

    def test_business_scoped_api_accepts_valid_explicit_context(self):
        self.client.credentials(HTTP_X_BUSINESS_ID=str(self.business.pk))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["inventory_enabled"], self.business.inventory_enabled)


    def test_user_can_resolve_each_of_multiple_active_business_contexts(self):
        second_business = BusinessService.create_business(self.user, "Second Tenant Cafe")
        first_context = resolve_tenant_context(
            user=self.user,
            business_id=self.business.pk,
        )
        second_context = resolve_tenant_context(
            user=self.user,
            business_id=second_business.pk,
        )
        self.assertNotEqual(first_context.business_id, second_context.business_id)
        self.assertEqual(
            Membership.objects.filter(user=self.user, is_active=True).count(),
            2,
        )


class TenantAPIViewCompatibilityTests(TestCase):
    def setUp(self):
        from rest_framework.test import APIClient

        self.client = APIClient()
        self.user = User.objects.create_user(
            email="tenant-compat@example.test",
            password="test-password",
            name="Tenant Compatibility User",
            number="tenant-compat-user",
        )
        self.business = BusinessService.create_business(
            self.user, "Compatibility Cafe"
        )
        self.client.force_authenticate(user=self.user)
        self.url = "/api/accounts/business/profile/"

    def test_legacy_endpoint_keeps_single_business_compatibility(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.business.pk)

    def test_legacy_endpoint_accepts_valid_explicit_business_header(self):
        self.client.credentials(
            HTTP_X_BUSINESS_ID=str(self.business.pk)
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.business.pk)

    def test_legacy_endpoint_rejects_unowned_explicit_business_header(self):
        other_business = Business.objects.create(name="Unowned Compatibility Cafe")
        self.client.credentials(
            HTTP_X_BUSINESS_ID=str(other_business.pk)
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "BUSINESS_ACCESS_DENIED")


class MeAPIViewBusinessContextTests(TestCase):
    def setUp(self):
        from rest_framework.test import APIClient

        self.client = APIClient()
        self.user = User.objects.create_user(
            email="me-context@example.test",
            password="test-password",
            name="Me Context User",
            number="me-context-user",
        )
        self.business = BusinessService.create_business(
            self.user, "Me Context Cafe"
        )
        self.client.force_authenticate(user=self.user)
        self.url = "/api/accounts/auth/me/"

    def test_single_membership_returns_business_and_permissions_without_header(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        active_business = response.data["active_business"]
        self.assertEqual(active_business["id"], self.business.pk)
        self.assertEqual(active_business["role"], "OWNER")
        self.assertEqual(active_business["slug"], self.business.slug)
        self.assertIn("orders.view", active_business["permissions"])
        self.assertIn("orders.create", active_business["permissions"])
        self.assertEqual(active_business["inventory_enabled"], self.business.inventory_enabled)

    def test_multiple_memberships_require_explicit_selection_for_active_business(self):
        BusinessService.create_business(self.user, "Second Me Context Cafe")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["active_business"])
        self.assertEqual(response.data["meta"]["business_count"], 2)

    def test_explicit_business_header_returns_only_selected_membership_permissions(self):
        second_business = BusinessService.create_business(
            self.user, "Second Selected Cafe"
        )
        second_membership = Membership.objects.get(
            user=self.user, business=second_business
        )
        from accounts.models import Permission, RolePermission

        orders_view = Permission.objects.get(code="orders.view")
        RolePermission.objects.filter(
            role=second_membership.role,
            permission=orders_view,
        ).delete()

        self.client.credentials(HTTP_X_BUSINESS_ID=str(second_business.pk))
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["active_business"]["id"], second_business.pk)
        self.assertNotIn(
            "orders.view",
            response.data["active_business"]["permissions"],
        )

    def test_unowned_explicit_business_header_is_rejected(self):
        other_business = Business.objects.create(name="Unowned Me Context Cafe")
        self.client.credentials(HTTP_X_BUSINESS_ID=str(other_business.pk))

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "BUSINESS_ACCESS_DENIED")
