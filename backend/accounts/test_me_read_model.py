from unittest import TestCase as UnitTestCase

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.application.get_me_read_model import GetMeReadModel
from accounts.application.me_read_model import (
    ActiveBusiness,
    MeBusinessAccessDeniedError,
    MeMembership,
)
from accounts.models import Business, Membership, User
from accounts.services.business_service import BusinessService


class FakeMeReadRepository:
    def __init__(self, memberships=(), active_businesses=None):
        self.memberships = tuple(memberships)
        self.active_businesses = active_businesses or {}
        self.requested_businesses = []

    def list_me_memberships(self, *, user_id):
        return self.memberships

    def get_active_business_summary(self, *, user_id, business_id):
        self.requested_businesses.append((user_id, business_id))
        return self.active_businesses.get((user_id, str(business_id))) or self.active_businesses.get(
            (user_id, business_id)
        )


class GetMeReadModelTests(UnitTestCase):
    def test_no_membership_returns_onboarding_context(self):
        result = GetMeReadModel(FakeMeReadRepository()).execute(user_id=7)

        self.assertFalse(result.has_business)
        self.assertTrue(result.needs_onboarding)
        self.assertEqual(result.business_count, 0)
        self.assertEqual(result.memberships, ())
        self.assertIsNone(result.active_business)

    def test_single_membership_is_selected_automatically(self):
        membership = MeMembership(business_id=12, business_name="Only Cafe", role="OWNER")
        active = ActiveBusiness(
            id=12, name="Only Cafe", role="OWNER", slug="only-cafe", logo=None,
            permissions=("orders.view",), inventory_enabled=False,
        )
        repository = FakeMeReadRepository(
            memberships=(membership,),
            active_businesses={(7, 12): active},
        )

        result = GetMeReadModel(repository).execute(user_id=7)

        self.assertEqual(result.active_business, active)
        self.assertEqual(repository.requested_businesses, [(7, 12)])

    def test_multiple_memberships_require_explicit_selection(self):
        memberships = (
            MeMembership(business_id=12, business_name="Alpha Cafe", role="OWNER"),
            MeMembership(business_id=13, business_name="Zulu Cafe", role="MANAGER"),
        )
        result = GetMeReadModel(FakeMeReadRepository(memberships=memberships)).execute(user_id=7)

        self.assertEqual(result.business_count, 2)
        self.assertEqual([item.business_name for item in result.memberships], ["Alpha Cafe", "Zulu Cafe"])
        self.assertIsNone(result.active_business)

    def test_explicit_business_must_be_an_active_membership_of_the_user(self):
        repository = FakeMeReadRepository(memberships=())
        with self.assertRaises(MeBusinessAccessDeniedError):
            GetMeReadModel(repository).execute(user_id=7, business_id="999")


class MeReadModelAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="me-read-model@example.test",
            password="test-password",
            name="Me Read Model",
            number="me-read-model",
        )
        self.client.force_authenticate(user=self.user)

    def create_business(self, name):
        return BusinessService.create_business(self.user, name)

    def test_empty_membership_list_keeps_onboarding_response(self):
        response = self.client.get("/api/accounts/auth/me/")

        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(response.data["has_business"])
        self.assertEqual(response.data["memberships"], [])
        self.assertIsNone(response.data["active_business"])
        self.assertEqual(response.data["meta"], {"needs_onboarding": True, "business_count": 0})

    def test_single_membership_is_automatically_selected(self):
        business = self.create_business("Only Cafe")

        response = self.client.get("/api/accounts/auth/me/")

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["meta"]["business_count"], 1)
        self.assertEqual(response.data["active_business"]["id"], business.id)
        self.assertEqual(response.data["active_business"]["role"], "OWNER")
        self.assertIn("permissions", response.data["active_business"])

    def test_multiple_memberships_are_ordered_and_require_explicit_selection(self):
        zulu = self.create_business("Zulu Cafe")
        self.create_business("Alpha Cafe")

        response = self.client.get("/api/accounts/auth/me/")

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["meta"]["business_count"], 2)
        self.assertEqual(
            [item["business_name"] for item in response.data["memberships"]],
            ["Alpha Cafe", "Zulu Cafe"],
        )
        self.assertIsNone(response.data["active_business"])

        selected = self.client.get(
            "/api/accounts/auth/me/",
            HTTP_X_BUSINESS_ID=str(zulu.id),
        )
        self.assertEqual(selected.status_code, 200, selected.data)
        self.assertEqual(selected.data["active_business"]["id"], zulu.id)
        self.assertEqual(selected.data["active_business"]["name"], "Zulu Cafe")

    def test_explicit_business_from_another_user_is_denied(self):
        other = User.objects.create_user(
            email="other-me-read-model@example.test",
            password="test-password",
            name="Other User",
            number="other-me-read-model",
        )
        foreign_business = BusinessService.create_business(other, "Foreign Cafe")

        response = self.client.get(
            "/api/accounts/auth/me/",
            HTTP_X_BUSINESS_ID=str(foreign_business.id),
        )

        self.assertEqual(response.status_code, 403)

    def test_inactive_membership_is_not_listed_or_selectable(self):
        business = self.create_business("Inactive Cafe")
        Membership.objects.filter(user=self.user, business=business).update(is_active=False)

        response = self.client.get("/api/accounts/auth/me/")

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["memberships"], [])
        self.assertFalse(response.data["has_business"])

        denied = self.client.get(
            "/api/accounts/auth/me/",
            HTTP_X_BUSINESS_ID=str(business.id),
        )
        self.assertEqual(denied.status_code, 403)

    def test_inactive_business_is_not_listed_or_selectable(self):
        business = self.create_business("Disabled Cafe")
        Business.objects.filter(pk=business.pk).update(is_active=False)

        response = self.client.get("/api/accounts/auth/me/")

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["memberships"], [])
        self.assertFalse(response.data["has_business"])

        denied = self.client.get(
            "/api/accounts/auth/me/",
            HTTP_X_BUSINESS_ID=str(business.id),
        )
        self.assertEqual(denied.status_code, 403)
