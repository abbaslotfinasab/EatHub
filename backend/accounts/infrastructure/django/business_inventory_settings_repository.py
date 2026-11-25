from accounts.models import Business


class DjangoBusinessInventorySettingsRepository:
    """Django ORM adapter scoped to the explicitly authorized business ID."""

    def set_inventory_enabled(self, *, business_id: int, enabled: bool) -> bool:
        updated = Business.objects.filter(pk=business_id).update(
            inventory_enabled=enabled,
        )
        return updated == 1
