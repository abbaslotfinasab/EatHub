from unittest.mock import Mock, patch
from unittest import TestCase as UnitTestCase

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.application.business_profile_update_result import (
    BusinessProfileUpdatePersistenceResult,
)
from accounts.application.update_business_profile import (
    BusinessProfileNotFoundError,
    UpdateBusinessProfile,
)
from accounts.infrastructure.django.business_profile_update_repository import (
    DjangoBusinessProfileUpdateRepository,
)
from accounts.models import Business, Membership, Role, User


class UpdateBusinessProfileTests(UnitTestCase):
    def setUp(self):
        self.repository = Mock()
        self.logo_storage = Mock()
        self.use_case = UpdateBusinessProfile(self.repository, self.logo_storage)

    def test_updates_only_supplied_fields_for_explicit_business(self):
        self.repository.update_profile.return_value = (
            BusinessProfileUpdatePersistenceResult(previous_logo_path=None)
        )

        self.use_case.execute(business_id=41, name="Updated Cafe")

        self.repository.update_profile.assert_called_once_with(
            business_id=41,
            changes={"name": "Updated Cafe"},
        )
        self.logo_storage.delete.assert_not_called()

    def test_does_not_persist_an_empty_partial_update(self):
        self.use_case.execute(business_id=41)

        self.repository.update_profile.assert_not_called()

    def test_deletes_old_logo_only_after_successful_replacement(self):
        self.repository.update_profile.return_value = (
            BusinessProfileUpdatePersistenceResult(
                previous_logo_path="uploads/businesses/logos/7/old.png"
            )
        )

        self.use_case.execute(
            business_id=41,
            logo_path="uploads/businesses/logos/7/new.png",
        )

        self.logo_storage.delete.assert_called_once_with(
            "uploads/businesses/logos/7/old.png"
        )

    def test_does_not_delete_logo_when_path_is_unchanged(self):
        self.repository.update_profile.return_value = (
            BusinessProfileUpdatePersistenceResult(
                previous_logo_path="uploads/businesses/logos/7/current.png"
            )
        )

        self.use_case.execute(
            business_id=41,
            logo_path="uploads/businesses/logos/7/current.png",
        )

        self.logo_storage.delete.assert_not_called()

    def test_clearing_logo_deletes_previous_file(self):
        self.repository.update_profile.return_value = (
            BusinessProfileUpdatePersistenceResult(
                previous_logo_path="uploads/businesses/logos/7/current.png"
            )
        )

        self.use_case.execute(business_id=41, logo_path=None)

        self.logo_storage.delete.assert_called_once_with(
            "uploads/businesses/logos/7/current.png"
        )

    def test_missing_business_does_not_delete_logo(self):
        self.repository.update_profile.return_value = None

        with self.assertRaises(BusinessProfileNotFoundError):
            self.use_case.execute(
                business_id=41,
                logo_path="uploads/businesses/logos/7/new.png",
            )

        self.logo_storage.delete.assert_not_called()


class DjangoBusinessProfileUpdateRepositoryTests(TestCase):
    def setUp(self):
        self.first = Business.objects.create(
            name="First Cafe",
            number="first",
            address="First Address",
        )
        self.second = Business.objects.create(
            name="Second Cafe",
            number="second",
            address="Second Address",
        )
        self.repository = DjangoBusinessProfileUpdateRepository()

    def test_update_is_scoped_to_the_requested_business_and_fields(self):
        result = self.repository.update_profile(
            business_id=self.first.pk,
            changes={"name": "Renamed Cafe"},
        )

        self.assertIsNotNone(result)
        self.first.refresh_from_db()
        self.second.refresh_from_db()
        self.assertEqual(self.first.name, "Renamed Cafe")
        self.assertEqual(self.first.number, "first")
        self.assertEqual(self.second.name, "Second Cafe")

    def test_logo_update_returns_previous_path_and_persists_new_path(self):
        old_path = "uploads/businesses/logos/1/old.png"
        new_path = "uploads/businesses/logos/1/new.png"
        self.first.logo = old_path
        self.first.save(update_fields=["logo"])

        result = self.repository.update_profile(
            business_id=self.first.pk,
            changes={"logo_path": new_path},
        )

        self.first.refresh_from_db()
        self.assertEqual(result.previous_logo_path, old_path)
        self.assertEqual(self.first.logo.name, new_path)

    def test_missing_business_returns_none(self):
        self.assertIsNone(
            self.repository.update_profile(
                business_id=999999,
                changes={"name": "Missing"},
            )
        )


class BusinessProfileUpdateAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email="business-profile-owner@example.test",
            password="test-password",
            name="Business Owner",
            number="biz-owner-01",
        )
        self.business = Business.objects.create(
            name="Original Business",
            number="original",
            address="Original Address",
        )
        owner_role = Role.objects.create(
            business=self.business,
            name="Owner",
            code="OWNER",
            is_system=True,
        )
        Membership.objects.create(
            user=self.owner,
            business=self.business,
            role=owner_role,
            is_active=True,
        )
        self.client.force_authenticate(user=self.owner)
        self.client.credentials(HTTP_X_BUSINESS_ID=str(self.business.pk))
        self.url = "/api/accounts/business/profile/"

    def test_patch_updates_only_supplied_fields_and_preserves_response_contract(self):
        response = self.client.patch(
            self.url,
            {"name": "Updated Business"},
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["name"], "Updated Business")
        self.assertEqual(response.data["number"], "original")
        self.assertEqual(response.data["address"], "Original Address")
        self.business.refresh_from_db()
        self.assertEqual(self.business.name, "Updated Business")

    def test_non_owner_cannot_update_business_profile(self):
        manager = User.objects.create_user(
            email="business-profile-manager@example.test",
            password="test-password",
            name="Business Manager",
            number="biz-manager-01",
        )
        manager_role = Role.objects.create(
            business=self.business,
            name="Manager",
            code="MANAGER",
            is_system=True,
        )
        Membership.objects.create(
            user=manager,
            business=self.business,
            role=manager_role,
            is_active=True,
        )
        self.client.force_authenticate(user=manager)

        response = self.client.patch(
            self.url,
            {"name": "Unauthorized Rename"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.business.refresh_from_db()
        self.assertEqual(self.business.name, "Original Business")

    def test_non_member_cannot_select_or_update_another_business(self):
        other_business = Business.objects.create(name="Unrelated Business")
        response = self.client.patch(
            self.url,
            {"name": "Cross Business Rename"},
            format="json",
            HTTP_X_BUSINESS_ID=str(other_business.pk),
        )

        self.assertEqual(response.status_code, 403)
        other_business.refresh_from_db()
        self.assertEqual(other_business.name, "Unrelated Business")

    def test_logo_path_must_be_scoped_to_authenticated_owner_upload_directory(self):
        invalid_path = "uploads/businesses/logos/another-user/logo.png"
        response = self.client.patch(
            self.url,
            {"logo": invalid_path},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.business.refresh_from_db()
        self.assertFalse(self.business.logo)

    def test_blank_logo_clears_existing_logo_and_deletes_old_file(self):
        old_path = f"uploads/businesses/logos/{self.owner.pk}/old.png"
        self.business.logo = old_path
        self.business.save(update_fields=["logo"])

        with patch("accounts.infrastructure.django.business_logo_storage.UploadService.delete") as delete:
            response = self.client.patch(
                self.url,
                {"logo": ""},
                format="json",
            )

        self.assertEqual(response.status_code, 200, response.data)
        self.business.refresh_from_db()
        self.assertFalse(self.business.logo)
        delete.assert_called_once_with(old_path)
