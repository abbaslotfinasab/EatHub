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
        self.assertIs(context.business, membership.business)
        self.assertIs(context.membership, membership)

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
