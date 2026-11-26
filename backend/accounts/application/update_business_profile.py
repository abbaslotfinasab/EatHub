from accounts.application.ports.business_logo_storage import BusinessLogoStorage
from accounts.application.ports.business_profile_update_repository import (
    BusinessProfileUpdateRepository,
)


_UNSET = object()


class BusinessProfileNotFoundError(Exception):
    """Raised when the selected business no longer exists."""


class UpdateBusinessProfile:
    """Update a business profile through persistence and storage ports."""

    def __init__(
        self,
        repository: BusinessProfileUpdateRepository,
        logo_storage: BusinessLogoStorage,
    ) -> None:
        self._repository = repository
        self._logo_storage = logo_storage

    def execute(
        self,
        *,
        business_id: int,
        name: str | object = _UNSET,
        number: str | object = _UNSET,
        address: str | object = _UNSET,
        logo_path: str | None | object = _UNSET,
    ) -> None:
        changes: dict[str, object] = {}
        if name is not _UNSET:
            changes["name"] = name
        if number is not _UNSET:
            changes["number"] = number
        if address is not _UNSET:
            changes["address"] = address
        if logo_path is not _UNSET:
            changes["logo_path"] = logo_path

        if not changes:
            return

        result = self._repository.update_profile(
            business_id=business_id,
            changes=changes,
        )
        if result is None:
            raise BusinessProfileNotFoundError()

        new_logo_path = changes.get("logo_path", _UNSET)
        if (
            new_logo_path is not _UNSET
            and result.previous_logo_path
            and result.previous_logo_path != new_logo_path
        ):
            self._logo_storage.delete(result.previous_logo_path)
