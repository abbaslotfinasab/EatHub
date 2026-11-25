from accounts.application.login_membership_read_model import LoginMembership
from accounts.application.ports.membership_read_repository import MembershipReadRepository


class ListLoginMemberships:
    """Return the authenticated user's eligible businesses for the login response."""

    def __init__(self, repository: MembershipReadRepository):
        self._repository = repository

    def execute(self, *, user_id: int) -> tuple[LoginMembership, ...]:
        return self._repository.list_login_memberships(user_id=user_id)
