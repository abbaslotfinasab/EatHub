from typing import Protocol


class UserAvatarStorage(Protocol):
    def delete(self, path: str) -> None:
        ...
