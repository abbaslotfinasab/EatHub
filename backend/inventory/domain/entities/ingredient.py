from dataclasses import dataclass

from inventory.domain.enums.ingredient import IngredientPreparationLevel
from inventory.domain.exceptions import InvalidIngredient
from inventory.domain.value_objects.unit import Unit


@dataclass(frozen=True, slots=True)
class Ingredient:
    id: int | None
    business_id: int
    name: str
    canonical_unit: Unit
    preparation_level: IngredientPreparationLevel = IngredientPreparationLevel.RAW
    is_active: bool = True

    def __post_init__(self) -> None:
        if self.id is not None and (
            isinstance(self.id, bool) or not isinstance(self.id, int) or self.id <= 0
        ):
            raise InvalidIngredient("Ingredient ID must be a positive integer.")
        if (
            isinstance(self.business_id, bool)
            or not isinstance(self.business_id, int)
            or self.business_id <= 0
        ):
            raise InvalidIngredient("Business ID must be a positive integer.")
        if not isinstance(self.name, str) or not self.name.strip():
            raise InvalidIngredient("Ingredient name is required.")
        if not isinstance(self.canonical_unit, Unit):
            raise InvalidIngredient("Ingredient requires a canonical Unit.")
        if not isinstance(self.preparation_level, IngredientPreparationLevel):
            raise InvalidIngredient("Ingredient preparation level is invalid.")
        if not isinstance(self.is_active, bool):
            raise InvalidIngredient("Ingredient active state must be boolean.")
        object.__setattr__(self, "name", self.name.strip())
