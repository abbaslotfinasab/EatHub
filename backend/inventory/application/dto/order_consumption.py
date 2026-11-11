from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OrderRequirementIngredientDTO:
    id: int
    business_id: int
    name: str
    canonical_unit: str
