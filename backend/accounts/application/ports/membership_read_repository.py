from typing import Protocol

from accounts.application.login_membership_read_model import LoginMembership
from accounts.application.me_read_model import ActiveBusiness, MeMembership


class MembershipReadRepository(Protocol):
    """Read-only persistence contract for resolving an authenticated user's tenant."""

    def get_active_membership(self, *, user_id: int, business_id: int):
        ...

    def list_active_memberships(self, *, user_id: int, limit: int):
        ...

    def list_role_permission_codes(self, *, role_id: int) -> tuple[str, ...]:
        ...

    def list_me_memberships(self, *, user_id: int) -> tuple[MeMembership, ...]:
        ...

    def get_active_business_summary(
        self, *, user_id: int, business_id: int | str
    ) -> ActiveBusiness | None:
        ...

    def list_login_memberships(self, *, user_id: int) -> tuple[LoginMembership, ...]:
        ...
