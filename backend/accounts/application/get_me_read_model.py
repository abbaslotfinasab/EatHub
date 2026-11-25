from accounts.application.me_read_model import (
    MeBusinessAccessDeniedError,
    MeReadModel,
)
from accounts.application.ports.membership_read_repository import MembershipReadRepository


class GetMeReadModel:
    """Build the authenticated user's profile and eligible business context."""

    def __init__(self, repository: MembershipReadRepository):
        self._repository = repository

    def execute(self, *, user_id: int, business_id: int | str | None = None) -> MeReadModel:
        memberships = self._repository.list_me_memberships(user_id=user_id)
        selected_business_id = business_id
        if not selected_business_id and len(memberships) == 1:
            selected_business_id = memberships[0].business_id

        active_business = None
        if selected_business_id:
            active_business = self._repository.get_active_business_summary(
                user_id=user_id,
                business_id=selected_business_id,
            )
            if active_business is None:
                raise MeBusinessAccessDeniedError()

        return MeReadModel(
            memberships=memberships,
            active_business=active_business,
        )
