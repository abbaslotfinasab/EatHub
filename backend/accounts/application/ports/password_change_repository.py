from typing import Protocol


class PasswordChangeRepository(Protocol):
    """Persistence boundary for changing an authenticated user's password."""

    def change_password(
        self,
        *,
        user_id: int,
        old_password: str,
        new_password: str,
    ) -> bool | None:
        """Return True on success, False for invalid old password, None if missing."""
        ...
