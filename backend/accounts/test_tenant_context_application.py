from types import SimpleNamespace
from unittest import TestCase

from accounts.application.tenant_context import (
    BusinessAccessDeniedError,
    BusinessContextRequiredError,
    TenantContextResolver,
)


class FakeMembershipReadRepository:
    def __init__(self):
        self.business = SimpleNamespace(pk=12, is_active=True)
        self.role = SimpleNamespace(pk=8, code="OWNER")
        self.membership = SimpleNamespace(
            pk=31,
            business_id=12,
            role_id=8,
            business=self.business,
            role=self.role,
        )
        self.memberships = [self.membership]
        self.permission_codes = ("orders.view", "orders.create")

    def get_active_membership(self, *, user_id, business_id):
        if user_id == 5 and str(business_id) == "12":
            return self.membership
        return None

    def list_active_memberships(self, *, user_id, limit):
        return self.memberships[:limit]

    def list_role_permission_codes(self, *, role_id):
        return self.permission_codes if role_id == 8 else ()


class TenantContextResolverUnitTests(TestCase):
    def setUp(self):
        self.repository = FakeMembershipReadRepository()
        self.resolver = TenantContextResolver(self.repository)

    def test_resolves_membership_and_permissions_without_orm_dependency(self):
        context = self.resolver.resolve(user_id=5, business_id="12")

        self.assertEqual(context.user_id, 5)
        self.assertEqual(context.business_id, 12)
        self.assertEqual(context.membership_id, 31)
        self.assertEqual(context.role_id, 8)
        self.assertEqual(context.permissions, ("orders.view", "orders.create"))
        self.assertIs(context.business, self.repository.business)
        self.assertIs(context.membership, self.repository.membership)

    def test_missing_business_context_is_rejected(self):
        with self.assertRaises(BusinessContextRequiredError):
            self.resolver.resolve(user_id=5, business_id=None)

    def test_unowned_or_inactive_membership_is_rejected(self):
        with self.assertRaises(BusinessAccessDeniedError):
            self.resolver.resolve(user_id=5, business_id=99)

    def test_compatibility_membership_reads_are_delegated_to_repository(self):
        self.assertEqual(self.resolver.list_active_memberships(user_id=5, limit=2), [self.repository.membership])
        self.assertIs(
            self.resolver.get_active_membership(user_id=5, business_id=12),
            self.repository.membership,
        )
        self.assertEqual(
            self.resolver.list_role_permission_codes(role_id=8),
            ("orders.view", "orders.create"),
        )
