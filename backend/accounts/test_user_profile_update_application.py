from unittest.mock import Mock, patch
from unittest import TestCase as UnitTestCase

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.application.update_user_profile import (
    UpdateUserProfile,
    UserProfileNotFoundError,
    UserProfileNumberAlreadyInUseError,
)
from accounts.application.user_profile_update_result import (
    UserProfileUpdatePersistenceResult,
)
from accounts.infrastructure.django.user_profile_update_repository import (
    DjangoUserProfileUpdateRepository,
)
from accounts.models import User


class UpdateUserProfileTests(UnitTestCase):
    def setUp(self):
        self.repository = Mock()
        self.avatar_storage = Mock()
        self.use_case = UpdateUserProfile(self.repository, self.avatar_storage)

    def test_updates_only_supplied_profile_fields(self):
        self.repository.update_profile.return_value = (
            UserProfileUpdatePersistenceResult(previous_avatar_path=None)
        )

        self.use_case.execute(user_id=17, name="Updated Name")

        self.repository.update_profile.assert_called_once_with(
            user_id=17,
            changes={"name": "Updated Name"},
        )
        self.repository.is_number_in_use.assert_not_called()
        self.avatar_storage.delete.assert_not_called()

    def test_rejects_a_phone_number_owned_by_another_user(self):
        self.repository.is_number_in_use.return_value = True

        with self.assertRaises(UserProfileNumberAlreadyInUseError):
            self.use_case.execute(user_id=17, number="taken")

        self.repository.update_profile.assert_not_called()

    def test_deletes_previous_avatar_only_after_successful_replacement(self):
        self.repository.update_profile.return_value = (
            UserProfileUpdatePersistenceResult(
                previous_avatar_path="uploads/avatars/17/old.png"
            )
        )

        self.use_case.execute(
            user_id=17,
            avatar_path="uploads/avatars/17/new.png",
        )

        self.avatar_storage.delete.assert_called_once_with(
            "uploads/avatars/17/old.png"
        )

    def test_does_not_delete_avatar_when_path_is_unchanged(self):
        self.repository.update_profile.return_value = (
            UserProfileUpdatePersistenceResult(
                previous_avatar_path="uploads/avatars/17/current.png"
            )
        )

        self.use_case.execute(
            user_id=17,
            avatar_path="uploads/avatars/17/current.png",
        )

        self.avatar_storage.delete.assert_not_called()

    def test_clearing_avatar_deletes_previous_file(self):
        self.repository.update_profile.return_value = (
            UserProfileUpdatePersistenceResult(
                previous_avatar_path="uploads/avatars/17/current.png"
            )
        )

        self.use_case.execute(user_id=17, avatar_path=None)

        self.avatar_storage.delete.assert_called_once_with(
            "uploads/avatars/17/current.png"
        )

    def test_missing_user_is_reported_without_deleting_avatar(self):
        self.repository.update_profile.return_value = None

        with self.assertRaises(UserProfileNotFoundError):
            self.use_case.execute(
                user_id=17,
                avatar_path="uploads/avatars/17/new.png",
            )

        self.avatar_storage.delete.assert_not_called()


class DjangoUserProfileUpdateRepositoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="profile-update@example.test",
            password="test-password",
            name="Profile User",
            number="profile-update-phone",
        )
        self.other_user = User.objects.create_user(
            email="profile-update-other@example.test",
            password="test-password",
            name="Other User",
            number="profile-update-other-phone",
        )
        self.repository = DjangoUserProfileUpdateRepository()

    def test_number_lookup_excludes_the_current_user(self):
        self.assertFalse(
            self.repository.is_number_in_use(
                number=self.user.number,
                exclude_user_id=self.user.pk,
            )
        )
        self.assertTrue(
            self.repository.is_number_in_use(
                number=self.other_user.number,
                exclude_user_id=self.user.pk,
            )
        )

    def test_update_changes_only_the_requested_user_and_fields(self):
        result = self.repository.update_profile(
            user_id=self.user.pk,
            changes={"name": "Changed Name"},
        )

        self.assertIsNotNone(result)
        self.user.refresh_from_db()
        self.other_user.refresh_from_db()
        self.assertEqual(self.user.name, "Changed Name")
        self.assertEqual(self.user.number, "profile-update-phone")
        self.assertEqual(self.other_user.name, "Other User")

    def test_update_avatar_returns_previous_path_and_sets_new_path(self):
        old_path = f"uploads/avatars/{self.user.pk}/old.png"
        new_path = f"uploads/avatars/{self.user.pk}/new.png"
        self.user.avatar = old_path
        self.user.save(update_fields=["avatar"])

        result = self.repository.update_profile(
            user_id=self.user.pk,
            changes={"avatar_path": new_path},
        )

        self.user.refresh_from_db()
        self.assertEqual(result.previous_avatar_path, old_path)
        self.assertEqual(self.user.avatar.name, new_path)

    def test_missing_user_returns_none(self):
        self.assertIsNone(
            self.repository.update_profile(
                user_id=999999,
                changes={"name": "Missing"},
            )
        )


class UserProfileUpdateAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="profile-update-api@example.test",
            password="test-password",
            name="API Profile User",
            number="profile-update-api-phone",
        )
        self.client.force_authenticate(user=self.user)
        self.url = "/api/accounts/auth/me/"

    def test_partial_profile_update_preserves_other_fields_and_response_contract(self):
        response = self.client.patch(
            self.url,
            {"name": "API Updated Name"},
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["name"], "API Updated Name")
        self.assertEqual(response.data["email"], "profile-update-api@example.test")
        self.user.refresh_from_db()
        self.assertEqual(self.user.number, "profile-update-api-phone")

    def test_avatar_clear_updates_profile_and_deletes_previous_file(self):
        old_path = f"uploads/avatars/{self.user.pk}/current.png"
        self.user.avatar = old_path
        self.user.save(update_fields=["avatar"])

        with patch(
            "accounts.infrastructure.django.user_avatar_storage.UploadService.delete"
        ) as delete_avatar:
            response = self.client.patch(
                self.url,
                {"avatar": ""},
                format="json",
            )

        self.assertEqual(response.status_code, 200, response.data)
        self.user.refresh_from_db()
        self.assertFalse(self.user.avatar)
        delete_avatar.assert_called_once_with(old_path)

    def test_profile_update_cannot_target_another_user(self):
        other = User.objects.create_user(
            email="profile-update-target@example.test",
            password="test-password",
            name="Target User",
            number="profile-update-target-phone",
        )

        response = self.client.patch(
            self.url,
            {"name": "Attacker Name", "user_id": other.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        other.refresh_from_db()
        self.assertEqual(other.name, "Target User")
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "Attacker Name")
