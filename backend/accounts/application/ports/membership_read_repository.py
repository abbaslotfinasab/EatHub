from typing import Protocol


class MembershipReadRepository(Protocol):
    """Read-only persistence contract for resolving an authenticated user's tenant."""

    def get_active_membership(self, *, user_id: int, business_id: int):
        ...

    def list_active_memberships(self, *, user_id: int, limit: int):
        ...

    def list_role_permission_codes(self, *, role_id: int) -> tuple[str, ...]:
        ...
