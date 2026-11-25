from accounts.application.ports.user_avatar_storage import UserAvatarStorage
from accounts.application.ports.user_profile_update_repository import (
    UserProfileUpdateRepository,
)


_UNSET = object()


class UserProfileNotFoundError(Exception):
    """Raised when the authenticated user no longer exists."""


class UserProfileNumberAlreadyInUseError(Exception):
    """Raised when another user already owns the requested phone number."""


class UpdateUserProfile:
    """Update an authenticated user's profile through persistence and storage ports."""

    def __init__(
        self,
        repository: UserProfileUpdateRepository,
        avatar_storage: UserAvatarStorage,
    ) -> None:
        self._repository = repository
        self._avatar_storage = avatar_storage

    def execute(
        self,
        *,
        user_id: int,
        name: str | object = _UNSET,
        number: str | object = _UNSET,
        avatar_path: str | None | object = _UNSET,
    ) -> None:
        changes: dict[str, object] = {}
        if name is not _UNSET:
            changes["name"] = name
        if number is not _UNSET:
            if self._repository.is_number_in_use(
                number=number, exclude_user_id=user_id
            ):
                raise UserProfileNumberAlreadyInUseError()
            changes["number"] = number
        if avatar_path is not _UNSET:
            changes["avatar_path"] = avatar_path

        if not changes:
            return

        result = self._repository.update_profile(
            user_id=user_id,
            changes=changes,
        )
        if result is None:
            raise UserProfileNotFoundError()

        new_avatar_path = changes.get("avatar_path", _UNSET)
        if (
            new_avatar_path is not _UNSET
            and result.previous_avatar_path
            and result.previous_avatar_path != new_avatar_path
        ):
            self._avatar_storage.delete(result.previous_avatar_path)
