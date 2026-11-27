from dataclasses import dataclass


@dataclass(frozen=True)
class BusinessTenantSummary:
    id: int
    name: str
    slug: str
    logo_url: str | None
    number: str | None
    address: str
    inventory_enabled: bool

    @property
    def pk(self) -> int:
        return self.id


@dataclass(frozen=True)
class MembershipTenantSummary:
    id: int
    business_id: int
    role_id: int
    role_code: str
    business: BusinessTenantSummary

    @property
    def pk(self) -> int:
        return self.id
