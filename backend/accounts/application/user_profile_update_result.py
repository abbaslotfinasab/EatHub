from dataclasses import dataclass


@dataclass(frozen=True)
class UserProfileUpdatePersistenceResult:
    previous_avatar_path: str | None
