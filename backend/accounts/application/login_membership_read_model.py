from dataclasses import dataclass


@dataclass(frozen=True)
class LoginMembership:
    business_id: int
    business_name: str
    role: str
