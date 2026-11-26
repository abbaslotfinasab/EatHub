from accounts.application.business_profile_update_result import (
    BusinessProfileUpdatePersistenceResult,
)
from accounts.models import Business


class DjangoBusinessProfileUpdateRepository:
    """Django ORM adapter for tenant-authorized business profile updates."""

    def update_profile(
        self, *, business_id: int, changes: dict[str, object]
    ) -> BusinessProfileUpdatePersistenceResult | None:
        business = Business.objects.filter(pk=business_id).first()
        if business is None:
            return None

        previous_logo_path = business.logo.name if business.logo else None
        update_fields: list[str] = []
        for field in ("name", "number", "address"):
            if field in changes:
                setattr(business, field, changes[field])
                update_fields.append(field)

        if "logo_path" in changes:
            business.logo = changes["logo_path"]
            update_fields.append("logo")

        if update_fields:
            update_fields.append("updated_at")
            business.save(update_fields=update_fields)

        return BusinessProfileUpdatePersistenceResult(
            previous_logo_path=previous_logo_path,
        )
