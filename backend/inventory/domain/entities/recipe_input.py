from dataclasses import dataclass

from inventory.domain.entities.ingredient import Ingredient
from inventory.domain.exceptions import InvalidRecipe
from inventory.domain.value_objects.quantity import Quantity


@dataclass(frozen=True, slots=True)
class RecipeInput:
    ingredient_id: int
    quantity: Quantity
    notes: str | None = None

    def __post_init__(self) -> None:
        if (
            isinstance(self.ingredient_id, bool)
            or not isinstance(self.ingredient_id, int)
            or self.ingredient_id <= 0
        ):
            raise InvalidRecipe("Recipe input requires an identified Ingredient.")
        if not isinstance(self.quantity, Quantity) or self.quantity.amount <= 0:
            raise InvalidRecipe("Recipe input quantity must be positive.")
        if self.notes is not None and not isinstance(self.notes, str):
            raise InvalidRecipe("Recipe input notes must be text or None.")

    @classmethod
    def for_ingredient(
        cls,
        ingredient: Ingredient,
        quantity: Quantity,
        notes: str | None = None,
    ) -> "RecipeInput":
        if ingredient.id is None:
            raise InvalidRecipe("Recipe input Ingredient must be identified.")
        if not isinstance(quantity, Quantity):
            raise InvalidRecipe("Recipe input requires a Quantity.")
        return cls(
            ingredient_id=ingredient.id,
            quantity=quantity.convert_to(ingredient.canonical_unit),
            notes=notes,
        )
