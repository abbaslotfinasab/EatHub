from typing import Protocol


class BusinessInventorySettingsRepository(Protocol):
    """Persistence contract for changing one business inventory setting."""

    def set_inventory_enabled(self, *, business_id: int, enabled: bool) -> bool:
        """Update the selected business and return whether it exists."""
        ...
