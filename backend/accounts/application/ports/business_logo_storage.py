from typing import Protocol


class BusinessLogoStorage(Protocol):
    def delete(self, path: str) -> None:
        ...
