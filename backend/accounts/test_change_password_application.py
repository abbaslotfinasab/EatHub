from unittest.mock import Mock
from unittest import TestCase as UnitTestCase

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.application.change_password import (
    ChangePassword,
    CurrentPasswordInvalidError,
    PasswordChangeUserNotFoundError,
)
from accounts.infrastructure.django.password_change_repository import (
    DjangoPasswordChangeRepository,
)
from accounts.models import User


class ChangePasswordTests(UnitTestCase):
    def setUp(self):
        self.repository = Mock()
        self.use_case = ChangePassword(self.repository)

    def test_changes_password_for_explicit_user_id(self):
        self.repository.change_password.return_value = True

        self.use_case.execute(
            user_id=17,
            old_password="current-password",
            new_password="new-password",
        )

        self.repository.change_password.assert_called_once_with(
            user_id=17,
            old_password="current-password",
            new_password="new-password",
        )

    def test_rejects_invalid_current_password(self):
        self.repository.change_password.return_value = False

        with self.assertRaises(CurrentPasswordInvalidError):
            self.use_case.execute(
                user_id=17,
                old_password="wrong-password",
                new_password="new-password",
            )

    def test_reports_missing_user(self):
        self.repository.change_password.return_value = None

        with self.assertRaises(PasswordChangeUserNotFoundError):
            self.use_case.execute(
                user_id=17,
                old_password="current-password",
                new_password="new-password",
            )


class DjangoPasswordChangeRepositoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="password-change@example.test",
            password="current-password",
            name="Password User",
            number="password-change-user",
        )
        self.repository = DjangoPasswordChangeRepository()

    def test_stores_new_password_as_hash_after_verifying_current_password(self):
        result = self.repository.change_password(
            user_id=self.user.pk,
            old_password="current-password",
            new_password="new-password",
        )

        self.assertTrue(result)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("new-password"))
        self.assertFalse(self.user.check_password("current-password"))
        self.assertNotEqual(self.user.password, "new-password")

    def test_invalid_current_password_does_not_change_password(self):
        old_hash = self.user.password

        result = self.repository.change_password(
            user_id=self.user.pk,
            old_password="wrong-password",
            new_password="new-password",
        )

        self.assertFalse(result)
        self.user.refresh_from_db()
        self.assertEqual(self.user.password, old_hash)

    def test_missing_user_returns_none(self):
        self.assertIsNone(
            self.repository.change_password(
                user_id=999999,
                old_password="current-password",
                new_password="new-password",
            )
        )


class ChangePasswordAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="password-change-api@example.test",
            password="current-password",
            name="Password API User",
            number="password-api-user",
        )
        self.client.force_authenticate(user=self.user)
        self.url = "/api/accounts/auth/change-password/"

    def test_authenticated_user_can_change_password(self):
        response = self.client.post(
            self.url,
            {
                "old_password": "current-password",
                "new_password": "new-password",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data, {"detail": "رمز عبور با موفقیت تغییر کرد."})
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("new-password"))

    def test_wrong_current_password_keeps_existing_password(self):
        response = self.client.post(
            self.url,
            {
                "old_password": "wrong-password",
                "new_password": "new-password",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("رمز عبور فعلی صحیح نیست.", str(response.data))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("current-password"))

    def test_new_password_minimum_length_is_preserved(self):
        response = self.client.post(
            self.url,
            {
                "old_password": "current-password",
                "new_password": "short",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("current-password"))
