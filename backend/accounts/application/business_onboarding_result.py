from dataclasses import dataclass


@dataclass(frozen=True)
class CreatedBusiness:
    business_id: int
    business_name: str
