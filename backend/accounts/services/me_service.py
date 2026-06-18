class MeService:

    @staticmethod
    def get_user_context(user, request=None):

        memberships = (
            user.memberships
            .select_related("business", "role")
            .filter(is_active=True)
        )

        has_business = memberships.exists()

        active_business = None

        # از middleware می‌گیریم (enterprise pattern)
        if request and getattr(request, "business", None):
            active_business = {
                "id": request.business.id,
                "name": request.business.name,
                "role": request.role.code,
            }

        return {
            "user": user,
            "memberships": memberships,
            "has_business": has_business,
            "active_business": active_business,
            "meta": {
                "needs_onboarding": not has_business,
                "business_count": memberships.count(),
            }
        }