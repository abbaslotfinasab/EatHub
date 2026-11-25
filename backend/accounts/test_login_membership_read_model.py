from unittest import TestCase as UnitTestCase

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.application.list_login_memberships import ListLoginMemberships
from accounts.application.login_membership_read_model import LoginMembership
from accounts.models import Business, Membership, User
from accounts.services.business_service import BusinessService


class FakeLoginMembershipRepository:
    def __init__(self, memberships=()):
        self.memberships = tuple(memberships)
        self.requested_user_ids = []

    def list_login_memberships(self, *, user_id):
        self.requested_user_ids.append(user_id)
        return self.memberships


class ListLoginMembershipsTests(UnitTestCase):
    def test_returns_repository_dtos_without_model_dependencies(self):
        memberships = (
            LoginMembership(business_id=3, business_name="First Cafe", role="OWNER"),
            LoginMembership(business_id=8, business_name="Second Cafe", role="MANAGER"),
        )
        repository = FakeLoginMembershipRepository(memberships)

        result = ListLoginMemberships(repository).execute(user_id=42)

        self.assertEqual(result, memberships)
        self.assertEqual(repository.requested_user_ids, [42])


class LoginMembershipsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="login-memberships@example.test",
            password="test-password",
            name="Login Memberships",
            number="login-memberships",
        )

    def create_business(self, name):
        return BusinessService.create_business(self.user, name)

    def login(self):
        return self.client.post(
            "/api/accounts/auth/login/",
            {"identifier": self.user.email, "password": "test-password"},
            format="json",
        )

    def test_login_without_businesses_returns_empty_business_list(self):
        response = self.login()

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["businesses"], [])

    def test_login_returns_active_businesses_in_business_name_order(self):
        second = self.create_business("Alpha Cafe")
        first = self.create_business("Zulu Cafe")

        response = self.login()

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            response.data["businesses"],
            [
                {"id": second.id, "name": "Alpha Cafe", "role": "OWNER"},
                {"id": first.id, "name": "Zulu Cafe", "role": "OWNER"},
            ],
        )

    def test_login_excludes_inactive_memberships_and_businesses(self):
        inactive_membership_business = self.create_business("Inactive Membership Cafe")
        inactive_business = self.create_business("Inactive Business Cafe")
        Membership.objects.filter(
            user=self.user,
            business=inactive_membership_business,
        ).update(is_active=False)
        Business.objects.filter(pk=inactive_business.pk).update(is_active=False)

        response = self.login()

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["businesses"], [])

    def test_invalid_credentials_keep_validation_error(self):
        response = self.client.post(
            "/api/accounts/auth/login/",
            {"identifier": self.user.email, "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"non_field_errors": ["Invalid credentials"]})
