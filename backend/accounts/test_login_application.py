from unittest import TestCase as UnitTestCase
from unittest.mock import Mock

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from accounts.application.authenticated_user import AuthenticatedUser
from accounts.application.login_user import LoginUser
from accounts.infrastructure.django.user_authentication_repository import (
    DjangoUserAuthenticationRepository,
)
from accounts.infrastructure.django.login_token_issuer import DjangoLoginTokenIssuer
from accounts.models import Business, Membership, Role, User


class LoginUserApplicationTests(UnitTestCase):
    def test_delegates_credentials_and_returns_scalar_identity(self):
        repository = Mock()
        expected = AuthenticatedUser(
            user_id=42,
            email="login@example.test",
            name="Login User",
            number="09120000042",
        )
        repository.authenticate_user.return_value = expected

        result = LoginUser(repository).execute(
            identifier="login@example.test",
            password="secret-pass",
        )

        self.assertEqual(result, expected)
        repository.authenticate_user.assert_called_once_with(
            identifier="login@example.test",
            password="secret-pass",
        )


class DjangoUserAuthenticationRepositoryTests(TestCase):
    def setUp(self):
        self.repository = DjangoUserAuthenticationRepository()
        self.user = User.objects.create_user(
            email="login-adapter@example.test",
            password="secret-pass",
            name="Login Adapter",
            number="09120000043",
        )

    def test_authenticates_email_and_returns_scalar_dto(self):
        result = self.repository.authenticate_user(
            identifier=self.user.email,
            password="secret-pass",
        )

        self.assertEqual(
            result,
            AuthenticatedUser(
                user_id=self.user.pk,
                email=self.user.email,
                name=self.user.name,
                number=self.user.number,
            ),
        )

    def test_authenticates_phone_using_configured_backend(self):
        result = self.repository.authenticate_user(
            identifier=self.user.number,
            password="secret-pass",
        )

        self.assertEqual(result.user_id, self.user.pk)

    def test_invalid_credentials_return_none(self):
        result = self.repository.authenticate_user(
            identifier=self.user.email,
            password="wrong-password",
        )

        self.assertIsNone(result)

    def test_inactive_user_remains_unauthenticated(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        result = self.repository.authenticate_user(
            identifier=self.user.email,
            password="secret-pass",
        )

        self.assertIsNone(result)


class DjangoLoginTokenIssuerTests(TestCase):
    def test_issues_existing_simplejwt_pair_for_user_id(self):
        user = User.objects.create_user(
            email="login-token@example.test",
            password="secret-pass",
            name="Login Token",
            number="09120000044",
        )

        access, refresh = DjangoLoginTokenIssuer().issue(user_id=user.pk)

        self.assertEqual(AccessToken(access)[api_settings.USER_ID_CLAIM], str(user.pk))
        self.assertEqual(RefreshToken(refresh)[api_settings.USER_ID_CLAIM], str(user.pk))


class LoginAPIViewTests(TestCase):
    url = "/api/accounts/auth/login/"

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="login-api@example.test",
            password="secret-pass",
            name="Login API",
            number="09120000045",
        )
        self.business = Business.objects.create(name="Login API Business")
        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            code="OWNER",
        )
        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=self.role,
            is_active=True,
        )

    def test_login_preserves_response_membership_and_jwt_contract(self):
        response = self.client.post(
            self.url,
            {"identifier": self.user.email, "password": "secret-pass"},
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            set(response.data),
            {"user", "access", "refresh", "businesses"},
        )
        self.assertEqual(
            response.data["user"],
            {
                "id": self.user.pk,
                "name": self.user.name,
                "number": self.user.number,
                "email": self.user.email,
            },
        )
        self.assertEqual(
            response.data["businesses"],
            [{"id": self.business.pk, "name": self.business.name, "role": "OWNER"}],
        )
        self.assertEqual(
            AccessToken(response.data["access"])[api_settings.USER_ID_CLAIM],
            str(self.user.pk),
        )
        self.assertEqual(
            RefreshToken(response.data["refresh"])[api_settings.USER_ID_CLAIM],
            str(self.user.pk),
        )

    def test_invalid_credentials_keep_existing_error(self):
        response = self.client.post(
            self.url,
            {"identifier": self.user.email, "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid credentials", str(response.data))
