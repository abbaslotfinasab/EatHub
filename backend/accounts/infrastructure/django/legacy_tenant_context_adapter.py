from accounts.models import Membership


class DjangoLegacyTenantContextAdapter:
    """Temporary ORM bridge for domain endpoints not migrated to tenant DTOs yet."""

    def get_active_membership(self, *, user_id: int, business_id: int):
        try:
            return Membership.objects.select_related("business", "role").get(
                user_id=user_id,
                business_id=business_id,
                is_active=True,
                business__is_active=True,
            )
        except (Membership.DoesNotExist, ValueError, TypeError):
            return None
