from accounts.application.ports.password_change_repository import (
    PasswordChangeRepository,
)


class PasswordChangeUserNotFoundError(Exception):
    """Raised when the authenticated user no longer exists."""


class CurrentPasswordInvalidError(Exception):
    """Raised when the supplied current password does not match."""


class ChangePassword:
    """Change a user's password through the persistence boundary."""

    def __init__(self, repository: PasswordChangeRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        user_id: int,
        old_password: str,
        new_password: str,
    ) -> None:
        result = self._repository.change_password(
            user_id=user_id,
            old_password=old_password,
            new_password=new_password,
        )
        if result is None:
            raise PasswordChangeUserNotFoundError()
        if not result:
            raise CurrentPasswordInvalidError()
