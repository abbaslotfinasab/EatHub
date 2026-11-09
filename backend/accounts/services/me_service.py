class MeService:

    @staticmethod
    def get_user_context(user, request=None):
        # Only eligible memberships are exposed. The selected business is tab-local
        # and must never be inferred from Membership.is_active.
        memberships = (
            user.memberships
            .select_related("business", "role")
            .filter(is_active=True, business__is_active=True)
            .order_by("business__name")
        )
        has_business = memberships.exists()
        active_business = None

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
