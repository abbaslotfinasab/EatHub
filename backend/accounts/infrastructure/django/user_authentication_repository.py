from django.contrib.auth import authenticate

from accounts.application.authenticated_user import AuthenticatedUser


class DjangoUserAuthenticationRepository:
    """Adapter that delegates to Django's configured authentication backends."""

    def authenticate_user(
        self, *, identifier: str, password: str
    ) -> AuthenticatedUser | None:
        user = authenticate(username=identifier, password=password)
        if user is None:
            return None
        return AuthenticatedUser(
            user_id=user.pk,
            email=user.email,
            name=user.name,
            number=user.number,
        )
