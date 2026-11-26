from accounts.application.authenticated_user import AuthenticatedUser
from accounts.application.ports.user_authentication_repository import (
    UserAuthenticationRepository,
)


class LoginUser:
    """Authenticate a user without exposing persistence models to callers."""

    def __init__(self, repository: UserAuthenticationRepository):
        self._repository = repository

    def execute(self, *, identifier: str, password: str) -> AuthenticatedUser | None:
        return self._repository.authenticate_user(
            identifier=identifier,
            password=password,
        )
