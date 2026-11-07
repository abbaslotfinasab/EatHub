class MeService:

    @staticmethod
    def get_user_context(user, request=None):
        # Membership history is intentionally retained for the business switcher.
        memberships = (
            user.memberships
            .select_related("business", "role")
            .filter(business__is_active=True)
            .order_by("-is_active", "business__name")
        )
        active_membership = memberships.filter(is_active=True).first()
        has_business = memberships.exists()

        active_business = None
        if active_membership:
            active_business = {
                "id": active_membership.business.id,
                "name": active_membership.business.name,
                "logo": active_membership.business.logo.url if active_membership.business.logo else None,
                "inventory_enabled": active_membership.business.inventory_enabled,
                "role": active_membership.role.code,
                "slug": active_membership.business.slug,
                "permissions": list(
                    active_membership.role.role_permissions
                    .select_related("permission")
                    .values_list("permission__code", flat=True)
                ),
            }

        return {
            "user": user,
            "memberships": memberships,
            "has_business": has_business,
            "active_business": active_business,
            "meta": {
                "needs_onboarding": not has_business,
                "business_count": memberships.count(),
            },
        }
