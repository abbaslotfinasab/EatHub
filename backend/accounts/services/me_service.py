from accounts.tenant_context import resolve_tenant_context


class MeService:

    @staticmethod
    def get_user_context(user, request=None):
        # Only eligible memberships are exposed. A tab-selected business is
        # resolved from the explicit header; a single membership remains
        # backwards-compatible without requiring a prior selection.
        memberships = (
            user.memberships
            .select_related("business", "role")
            .filter(is_active=True, business__is_active=True)
            .order_by("business__name")
        )
        has_business = memberships.exists()
        business_count = memberships.count()
        business_id = (
            request.headers.get("X-Business-Id")
            if request is not None
            else None
        )

        if not business_id and business_count == 1:
            business_id = memberships.values_list("business_id", flat=True).first()

        active_business = None
        if business_id:
            tenant_context = resolve_tenant_context(
                user=user,
                business_id=business_id,
            )
            business = tenant_context.business
            active_business = {
                "id": business.pk,
                "name": business.name,
                "role": tenant_context.membership.role.code,
                "slug": business.slug,
                "logo": business.logo.url if business.logo else None,
                "permissions": list(tenant_context.permissions),
                "inventory_enabled": business.inventory_enabled,
            }

        return {
            "user": user,
            "memberships": memberships,
            "has_business": has_business,
            "active_business": active_business,
            "meta": {
                "needs_onboarding": not has_business,
                "business_count": business_count,
            },
        }
