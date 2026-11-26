from unittest import TestCase as UnitTestCase
from unittest.mock import Mock

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from accounts.application.user_registration import (
    RegisterUser,
    RegistrationEmailAlreadyExistsError,
    RegistrationNumberAlreadyExistsError,
)
from accounts.infrastructure.django.user_registration_repository import (
    DjangoUserRegistrationRepository,
)
from accounts.models import User


class RegisterUserApplicationTests(UnitTestCase):
    def setUp(self):
        self.repository = Mock()
        self.use_case = RegisterUser(self.repository)

    def test_registers_with_explicit_input_and_returns_identity_dto(self):
        from accounts.application.user_registration import RegisteredUser

        expected = RegisteredUser(
            user_id=12,
            email="new@example.test",
            name="New User",
            number="09120000000",
        )
        self.repository.register_user.return_value = expected

        result = self.use_case.execute(
            email="new@example.test",
            password="secret-pass",
            name="New User",
            number="09120000000",
        )

        self.assertEqual(result, expected)
        self.repository.register_user.assert_called_once_with(
            email="new@example.test",
            password="secret-pass",
            name="New User",
            number="09120000000",
        )


class DjangoUserRegistrationRepositoryTests(TestCase):
    def setUp(self):
        self.repository = DjangoUserRegistrationRepository()

    def test_creates_user_with_normalized_email_and_hashed_password(self):
        result = self.repository.register_user(
            email="new-user@EXAMPLE.TEST",
            password="secret-pass",
            name="New User",
            number="09120000001",
        )

        user = User.objects.get(pk=result.user_id)
        self.assertEqual(result.email, "new-user@example.test")
        self.assertEqual(user.email, "new-user@example.test")
        self.assertTrue(user.check_password("secret-pass"))
        self.assertNotEqual(user.password, "secret-pass")
        self.assertEqual(result.name, "New User")
        self.assertEqual(result.number, "09120000001")

    def test_rejects_duplicate_email(self):
        User.objects.create_user(
            email="existing@example.test",
            password="secret-pass",
            name="Existing",
            number="09120000002",
        )

        with self.assertRaises(RegistrationEmailAlreadyExistsError):
            self.repository.register_user(
                email="existing@example.test",
                password="another-pass",
                name="Duplicate Email",
                number="09120000003",
            )

        self.assertEqual(User.objects.count(), 1)

    def test_rejects_duplicate_number(self):
        User.objects.create_user(
            email="existing-number@example.test",
            password="secret-pass",
            name="Existing",
            number="09120000004",
        )

        with self.assertRaises(RegistrationNumberAlreadyExistsError):
            self.repository.register_user(
                email="new@example.test",
                password="another-pass",
                name="Duplicate Number",
                number="09120000004",
            )

        self.assertFalse(User.objects.filter(email="new@example.test").exists())


class RegisterUserAPITests(TestCase):
    url = "/api/accounts/auth/register/"

    def setUp(self):
        self.client = APIClient()
        self.payload = {
            "email": "registration@example.test",
            "password": "secret-pass",
            "name": "Registration User",
            "number": "09120000005",
        }

    def test_registration_preserves_response_and_jwt_contract(self):
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            set(response.data),
            {"user", "access", "refresh"},
        )
        user = User.objects.get(email="registration@example.test")
        self.assertEqual(
            response.data["user"],
            {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "number": user.number,
            },
        )
        self.assertTrue(user.check_password("secret-pass"))
        self.assertNotEqual(user.password, "secret-pass")
        self.assertEqual(
            AccessToken(response.data["access"])[api_settings.USER_ID_CLAIM],
            str(user.pk),
        )
        self.assertEqual(
            RefreshToken(response.data["refresh"])[api_settings.USER_ID_CLAIM],
            str(user.pk),
        )

    def test_duplicate_email_keeps_existing_validation_message(self):
        User.objects.create_user(
            email=self.payload["email"],
            password="secret-pass",
            name="Existing",
            number="09120000006",
        )

        payload = {**self.payload, "email": "registration@EXAMPLE.TEST"}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("Email already exists", str(response.data))
        self.assertEqual(User.objects.count(), 1)

    def test_duplicate_number_keeps_existing_validation_message(self):
        User.objects.create_user(
            email="existing-number@example.test",
            password="secret-pass",
            name="Existing",
            number=self.payload["number"],
        )

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("Number already exists", str(response.data))
        self.assertFalse(User.objects.filter(email=self.payload["email"]).exists())

    def test_invalid_password_does_not_create_user(self):
        payload = {**self.payload, "password": "short"}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email=self.payload["email"]).exists())
