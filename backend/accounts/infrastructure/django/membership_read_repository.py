from django.core.exceptions import ObjectDoesNotExist

from accounts.application.me_read_model import ActiveBusiness, MeMembership
from accounts.models import Membership, RolePermission


class DjangoMembershipReadRepository:
    """Django ORM adapter for authenticated membership and role-permission reads."""

    def get_active_membership(self, *, user_id: int, business_id: int):
        try:
            return (
                Membership.objects.select_related("business", "role")
                .get(
                    user_id=user_id,
                    business_id=business_id,
                    is_active=True,
                    business__is_active=True,
                )
            )
        except (ObjectDoesNotExist, ValueError, TypeError):
            return None

    def list_active_memberships(self, *, user_id: int, limit: int):
        return list(
            Membership.objects.select_related("business", "role")
            .filter(
                user_id=user_id,
                is_active=True,
                business__is_active=True,
            )
            .order_by("id")[:limit]
        )

    def list_role_permission_codes(self, *, role_id: int) -> tuple[str, ...]:
        return tuple(
            RolePermission.objects.filter(role_id=role_id)
            .select_related("permission")
            .values_list("permission__code", flat=True)
        )

    def list_me_memberships(self, *, user_id: int) -> tuple[MeMembership, ...]:
        memberships = (
            Membership.objects.select_related("business", "role")
            .filter(
                user_id=user_id,
                is_active=True,
                business__is_active=True,
            )
            .order_by("business__name")
        )
        return tuple(
            MeMembership(
                business_id=membership.business_id,
                business_name=membership.business.name,
                role=membership.role.code,
            )
            for membership in memberships
        )

    def get_active_business_summary(
        self, *, user_id: int, business_id: int | str
    ) -> ActiveBusiness | None:
        try:
            membership = (
                Membership.objects.select_related("business", "role")
                .get(
                    user_id=user_id,
                    business_id=business_id,
                    is_active=True,
                    business__is_active=True,
                )
            )
        except (ObjectDoesNotExist, ValueError, TypeError):
            return None

        business = membership.business
        return ActiveBusiness(
            id=business.pk,
            name=business.name,
            role=membership.role.code,
            slug=business.slug,
            logo=business.logo.url if business.logo else None,
            permissions=self.list_role_permission_codes(role_id=membership.role_id),
            inventory_enabled=business.inventory_enabled,
        )
