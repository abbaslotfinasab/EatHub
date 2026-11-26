from dataclasses import dataclass

from accounts.application.me_read_model import ActiveBusiness
from accounts.application.ports.membership_read_repository import MembershipReadRepository


@dataclass(frozen=True)
class SelectedBusiness:
    business_id: int
    business_name: str
    role: str


class SelectedBusinessNotFoundError(Exception):
    """The user has no active membership in the requested business."""


class SelectBusiness:
    """Resolve a user's active business selection into a presentation-safe DTO."""

    def __init__(self, membership_repository: MembershipReadRepository):
        self._membership_repository = membership_repository

    def execute(self, *, user_id: int, business_id: int | str) -> SelectedBusiness:
        business: ActiveBusiness | None = self._membership_repository.get_active_business_summary(
            user_id=user_id,
            business_id=business_id,
        )
        if business is None:
            raise SelectedBusinessNotFoundError()

        return SelectedBusiness(
            business_id=business.id,
            business_name=business.name,
            role=business.role,
        )
