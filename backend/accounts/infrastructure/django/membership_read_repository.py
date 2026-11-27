from django.core.exceptions import ObjectDoesNotExist

from accounts.application.login_membership_read_model import LoginMembership
from accounts.application.me_read_model import ActiveBusiness, MeMembership
from accounts.application.tenant_context_read_model import (
    BusinessTenantSummary,
    MembershipTenantSummary,
)
from accounts.models import Membership, RolePermission


class DjangoMembershipReadRepository:
    """Django ORM adapter; only scalar DTOs cross the application boundary."""

    @staticmethod
    def _to_tenant_summary(membership: Membership) -> MembershipTenantSummary:
        business = membership.business
        return MembershipTenantSummary(
            id=membership.pk,
            business_id=membership.business_id,
            role_id=membership.role_id,
            role_code=membership.role.code,
            business=BusinessTenantSummary(
                id=business.pk,
                name=business.name,
                slug=business.slug,
                logo_url=business.logo.url if business.logo else None,
                number=business.number,
                address=business.address,
                inventory_enabled=business.inventory_enabled,
            ),
        )

    def get_active_membership(
        self, *, user_id: int, business_id: int | str
    ) -> MembershipTenantSummary | None:
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
        return self._to_tenant_summary(membership)

    def list_active_memberships(
        self, *, user_id: int, limit: int
    ) -> tuple[MembershipTenantSummary, ...]:
        memberships = (
            Membership.objects.select_related("business", "role")
            .filter(
                user_id=user_id,
                is_active=True,
                business__is_active=True,
            )
            .order_by("id")[:limit]
        )
        return tuple(self._to_tenant_summary(membership) for membership in memberships)

    def list_role_permission_codes(self, *, role_id: int) -> tuple[str, ...]:
        return tuple(
            RolePermission.objects.filter(role_id=role_id)
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

    def list_login_memberships(self, *, user_id: int) -> tuple[LoginMembership, ...]:
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
            LoginMembership(
                business_id=membership.business_id,
                business_name=membership.business.name,
                role=membership.role.code,
            )
            for membership in memberships
        )
