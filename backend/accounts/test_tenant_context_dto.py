from dataclasses import replace
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.application.tenant_context import TenantContextResolver
from accounts.application.tenant_context_read_model import MembershipTenantSummary
from accounts.infrastructure.django.membership_read_repository import (
    DjangoMembershipReadRepository,
)
from accounts.models import Business, Membership, User
from accounts.services.business_service import BusinessService


class TenantContextDtoRepositoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="tenant-dto@example.test",
            password="test-password",
            name="Tenant DTO User",
            number="tenant-dto-user",
        )
        self.business = BusinessService.create_business(
            self.user, "Tenant DTO Cafe"
        )
        self.repository = DjangoMembershipReadRepository()

    def test_repository_returns_scalar_membership_and_business_dtos(self):
        membership = self.repository.get_active_membership(
            user_id=self.user.pk,
            business_id=self.business.pk,
        )

        self.assertIsInstance(membership, MembershipTenantSummary)
        self.assertEqual(membership.business_id, self.business.pk)
        self.assertEqual(membership.role_code, "OWNER")
        self.assertEqual(membership.business.id, self.business.pk)
        self.assertEqual(membership.business.name, self.business.name)
        self.assertFalse(hasattr(membership, "_meta"))
        self.assertFalse(hasattr(membership.business, "_meta"))

    def test_application_context_contains_only_scalar_dtos(self):
        context = TenantContextResolver(self.repository).resolve(
            user_id=self.user.pk,
            business_id=self.business.pk,
        )

        self.assertEqual(context.business_id, self.business.pk)
        self.assertEqual(context.membership_id, Membership.objects.get(
            user=self.user, business=self.business
        ).pk)
        self.assertEqual(context.role_code, "OWNER")
        self.assertIn("orders.view", context.permissions)
        self.assertFalse(hasattr(context.business, "_meta"))
        self.assertFalse(hasattr(context.membership, "_meta"))

    def test_membership_listing_returns_only_active_business_dtos(self):
        inactive_business = Business.objects.create(
            name="Inactive DTO Business",
            is_active=False,
        )
        Membership.objects.create(
            user=self.user,
            business=inactive_business,
            role=Membership.objects.get(
                user=self.user, business=self.business
            ).role,
            is_active=True,
        )

        memberships = self.repository.list_active_memberships(
            user_id=self.user.pk,
            limit=10,
        )

        self.assertEqual(len(memberships), 1)
        self.assertEqual(memberships[0].business_id, self.business.pk)
        self.assertTrue(all(isinstance(item, MembershipTenantSummary) for item in memberships))


class DtoTenantBusinessApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="tenant-dto-api@example.test",
            password="test-password",
            name="Tenant DTO API User",
            number="tenant-dto-api-user",
        )
        self.business = BusinessService.create_business(
            self.user, "Tenant DTO API Cafe"
        )
        self.client.force_authenticate(user=self.user)
        self.profile_url = "/api/accounts/business/profile/"
        self.inventory_url = "/api/accounts/business/inventory-settings/"

    def test_profile_endpoint_uses_dto_context_and_preserves_response_shape(self):
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data),
            {"id", "name", "slug", "logo", "number", "address"},
        )
        self.assertEqual(response.data["id"], self.business.pk)
        self.assertEqual(response.data["name"], self.business.name)

    def test_profile_patch_updates_selected_business_and_returns_fresh_dto(self):
        response = self.client.patch(
            self.profile_url,
            {"name": "Updated DTO Cafe"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Updated DTO Cafe")
        self.business.refresh_from_db()
        self.assertEqual(self.business.name, "Updated DTO Cafe")

    def test_profile_requires_header_for_multiple_businesses(self):
        BusinessService.create_business(self.user, "Second DTO Cafe")

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "BUSINESS_CONTEXT_REQUIRED")

    def test_profile_rejects_unowned_business_header(self):
        other_business = Business.objects.create(name="Other DTO Tenant")
        self.client.credentials(HTTP_X_BUSINESS_ID=str(other_business.pk))

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "BUSINESS_ACCESS_DENIED")

    def test_profile_patch_remains_owner_only(self):
        from accounts.views import resolve_tenant_context as original_resolver

        def non_owner_context(**kwargs):
            return replace(original_resolver(**kwargs), role_code="MANAGER")

        with patch("accounts.views.resolve_tenant_context", side_effect=non_owner_context):
            response = self.client.patch(
                self.profile_url,
                {"name": "Must Not Update"},
                format="json",
            )

        self.assertEqual(response.status_code, 403)
        self.business.refresh_from_db()
        self.assertEqual(self.business.name, "Tenant DTO API Cafe")

    def test_inventory_settings_requires_explicit_context_and_preserves_patch(self):
        missing_header = self.client.get(self.inventory_url)
        self.assertEqual(missing_header.status_code, 400)
        self.assertEqual(missing_header.data["code"], "BUSINESS_CONTEXT_REQUIRED")

        self.client.credentials(HTTP_X_BUSINESS_ID=str(self.business.pk))
        response = self.client.get(self.inventory_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["inventory_enabled"],
            self.business.inventory_enabled,
        )

        updated = self.client.patch(
            self.inventory_url,
            {"inventory_enabled": False},
            format="json",
        )
        self.assertEqual(updated.status_code, 200)
        self.assertFalse(updated.data["inventory_enabled"])
        self.business.refresh_from_db()
        self.assertFalse(self.business.inventory_enabled)

    def test_inventory_settings_rejects_unowned_business(self):
        other_business = Business.objects.create(name="Unowned Inventory Tenant")
        self.client.credentials(HTTP_X_BUSINESS_ID=str(other_business.pk))

        response = self.client.get(self.inventory_url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "BUSINESS_ACCESS_DENIED")
