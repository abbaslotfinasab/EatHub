from dataclasses import dataclass


@dataclass(frozen=True)
class MeMembership:
    business_id: int
    business_name: str
    role: str


@dataclass(frozen=True)
class ActiveBusiness:
    id: int
    name: str
    role: str
    slug: str
    logo: str | None
    permissions: tuple[str, ...]
    inventory_enabled: bool


@dataclass(frozen=True)
class MeReadModel:
    memberships: tuple[MeMembership, ...]
    active_business: ActiveBusiness | None

    @property
    def has_business(self) -> bool:
        return bool(self.memberships)

    @property
    def business_count(self) -> int:
        return len(self.memberships)

    @property
    def needs_onboarding(self) -> bool:
        return not self.has_business


class MeBusinessAccessDeniedError(Exception):
    """The authenticated user cannot access the requested business."""
