from unittest import TestCase as UnitTestCase

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.application.me_read_model import ActiveBusiness
from accounts.application.select_business import (
    SelectBusiness,
    SelectedBusiness,
    SelectedBusinessNotFoundError,
)
from accounts.models import Business, Membership, User
from accounts.services.business_service import BusinessService


class FakeMembershipReadRepository:
    def __init__(self, businesses=None):
        self.businesses = businesses or {}
        self.requested = []

    def get_active_business_summary(self, *, user_id, business_id):
        self.requested.append((user_id, business_id))
        return self.businesses.get((user_id, str(business_id)))


class SelectBusinessUseCaseTests(UnitTestCase):
    def test_returns_scalar_selection_dto_from_repository_read_model(self):
        summary = ActiveBusiness(
            id=12,
            name="Selected Cafe",
            role="OWNER",
            slug="selected-cafe",
            logo=None,
            permissions=("orders.view",),
            inventory_enabled=True,
        )
        repository = FakeMembershipReadRepository({(5, "12"): summary})

        result = SelectBusiness(repository).execute(user_id=5, business_id="12")

        self.assertEqual(
            result,
            SelectedBusiness(
                business_id=12,
                business_name="Selected Cafe",
                role="OWNER",
            ),
        )
        self.assertEqual(repository.requested, [(5, "12")])

    def test_missing_membership_raises_application_error(self):
        with self.assertRaises(SelectedBusinessNotFoundError):
            SelectBusiness(FakeMembershipReadRepository()).execute(
                user_id=5,
                business_id="99",
            )


class SelectBusinessAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="select-business@example.test",
            password="test-password",
            name="Select Business",
            number="select-business",
        )
        self.client.force_authenticate(user=self.user)
        self.url = "/api/accounts/auth/select-business/"

    def create_business(self, user, name):
        return BusinessService.create_business(user, name)

    def test_select_business_preserves_response_contract_for_active_membership(self):
        business = self.create_business(self.user, "Selected Cafe")

        response = self.client.post(
            self.url,
            {"business_id": str(business.pk)},
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            response.data,
            {
                "business": {"id": business.pk, "name": "Selected Cafe"},
                "role": "OWNER",
            },
        )

    def test_select_business_requires_business_id(self):
        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"business_id": "This field is required."})

    def test_select_business_rejects_membership_owned_by_another_user(self):
        other = User.objects.create_user(
            email="select-business-other@example.test",
            password="test-password",
            name="Other User",
            number="other-user",
        )
        foreign_business = self.create_business(other, "Foreign Cafe")

        response = self.client.post(
            self.url,
            {"business_id": str(foreign_business.pk)},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {"detail": "Invalid or inactive business membership"},
        )

    def test_select_business_rejects_inactive_membership(self):
        business = self.create_business(self.user, "Inactive Membership Cafe")
        Membership.objects.filter(user=self.user, business=business).update(is_active=False)

        response = self.client.post(
            self.url,
            {"business_id": str(business.pk)},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {"detail": "Invalid or inactive business membership"},
        )

    def test_select_business_rejects_inactive_business(self):
        business = self.create_business(self.user, "Inactive Business Cafe")
        Business.objects.filter(pk=business.pk).update(is_active=False)

        response = self.client.post(
            self.url,
            {"business_id": str(business.pk)},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {"detail": "Invalid or inactive business membership"},
        )

    def test_select_business_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(
            self.url,
            {"business_id": "12"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)
