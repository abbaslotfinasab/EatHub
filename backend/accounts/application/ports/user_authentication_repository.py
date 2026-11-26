from typing import Protocol

from accounts.application.authenticated_user import AuthenticatedUser


class UserAuthenticationRepository(Protocol):
    """Authenticate credentials using the configured identity provider."""

    def authenticate_user(
        self, *, identifier: str, password: str
    ) -> AuthenticatedUser | None:
        ...
