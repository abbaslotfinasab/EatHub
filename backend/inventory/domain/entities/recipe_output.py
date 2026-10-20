from dataclasses import dataclass

from inventory.domain.entities.ingredient import Ingredient
from inventory.domain.exceptions import InvalidRecipe
from inventory.domain.value_objects.quantity import Quantity


@dataclass(frozen=True, slots=True)
class RecipeOutput:
    ingredient_id: int
    quantity: Quantity
    is_primary: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        if (
            isinstance(self.ingredient_id, bool)
            or not isinstance(self.ingredient_id, int)
            or self.ingredient_id <= 0
        ):
            raise InvalidRecipe("Recipe output requires an identified Ingredient.")
        if not isinstance(self.quantity, Quantity) or self.quantity.amount <= 0:
            raise InvalidRecipe("Recipe output quantity must be positive.")
        if not isinstance(self.is_primary, bool):
            raise InvalidRecipe("Recipe output primary flag must be boolean.")
        if self.notes is not None and not isinstance(self.notes, str):
            raise InvalidRecipe("Recipe output notes must be text or None.")

    @classmethod
    def for_ingredient(
        cls,
        ingredient: Ingredient,
        quantity: Quantity,
        is_primary: bool = False,
        notes: str | None = None,
    ) -> "RecipeOutput":
        if ingredient.id is None:
            raise InvalidRecipe("Recipe output Ingredient must be identified.")
        if not isinstance(quantity, Quantity):
            raise InvalidRecipe("Recipe output requires a Quantity.")
        return cls(
            ingredient_id=ingredient.id,
            quantity=quantity.convert_to(ingredient.canonical_unit),
            is_primary=is_primary,
            notes=notes,
        )
