from dataclasses import dataclass

from accounts.application.ports.membership_read_repository import (
    MembershipReadRepository,
)


@dataclass(frozen=True)
class TenantContext:
    user_id: int
    business_id: int
    membership_id: int
    role_id: int
    permissions: tuple[str, ...]
    business: object
    membership: object


class BusinessContextRequiredError(Exception):
    """An explicit business selector is required for this request."""


class BusinessAccessDeniedError(Exception):
    """The user has no active membership in the requested business."""


class TenantContextResolver:
    """Application service for resolving authorized business context."""

    def __init__(self, membership_repository: MembershipReadRepository):
        self._membership_repository = membership_repository

    def resolve(self, *, user_id: int, business_id: int | str | None) -> TenantContext:
        if not business_id:
            raise BusinessContextRequiredError()

        membership = self._membership_repository.get_active_membership(
            user_id=user_id,
            business_id=business_id,
        )
        if membership is None:
            raise BusinessAccessDeniedError()

        permissions = self._membership_repository.list_role_permission_codes(
            role_id=membership.role_id,
        )
        return TenantContext(
            user_id=user_id,
            business_id=membership.business_id,
            membership_id=membership.pk,
            role_id=membership.role_id,
            permissions=permissions,
            business=membership.business,
            membership=membership,
        )

    def list_active_memberships(self, *, user_id: int, limit: int):
        return self._membership_repository.list_active_memberships(
            user_id=user_id,
            limit=limit,
        )

    def get_active_membership(self, *, user_id: int, business_id: int | str):
        return self._membership_repository.get_active_membership(
            user_id=user_id,
            business_id=business_id,
        )

    def list_role_permission_codes(self, *, role_id: int) -> tuple[str, ...]:
        return self._membership_repository.list_role_permission_codes(
            role_id=role_id,
        )
