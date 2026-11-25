from accounts.application.ports.business_inventory_settings_repository import (
    BusinessInventorySettingsRepository,
)


class BusinessInventoryBusinessNotFoundError(Exception):
    """The selected business no longer exists."""


class UpdateBusinessInventorySettings:
    """Use case for changing the inventory mode of one business."""

    def __init__(self, repository: BusinessInventorySettingsRepository):
        self._repository = repository

    def execute(self, *, business_id: int, inventory_enabled: bool) -> bool:
        updated = self._repository.set_inventory_enabled(
            business_id=business_id,
            enabled=inventory_enabled,
        )
        if not updated:
            raise BusinessInventoryBusinessNotFoundError()
        return inventory_enabled
