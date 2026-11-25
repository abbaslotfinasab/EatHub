from typing import Protocol

from accounts.application.user_profile_update_result import (
    UserProfileUpdatePersistenceResult,
)


class UserProfileUpdateRepository(Protocol):
    def is_number_in_use(self, *, number: str, exclude_user_id: int) -> bool:
        ...

    def update_profile(
        self, *, user_id: int, changes: dict[str, object]
    ) -> UserProfileUpdatePersistenceResult | None:
        ...
