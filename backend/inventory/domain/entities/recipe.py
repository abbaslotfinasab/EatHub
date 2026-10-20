from inventory.domain.entities.ingredient import Ingredient
from inventory.domain.entities.recipe_input import RecipeInput
from inventory.domain.entities.recipe_output import RecipeOutput
from inventory.domain.enums.recipe import RecipeType
from inventory.domain.exceptions import InvalidRecipe, TenantMismatch
from inventory.domain.value_objects.quantity import Quantity


class Recipe:
    """Recipe aggregate; its ingredient lines are owned value-like children."""

    __slots__ = (
        "_id",
        "_business_id",
        "_name",
        "_recipe_type",
        "_inputs",
        "_outputs",
        "_input_ingredients",
        "_output_ingredients",
    )

    def __init__(
        self,
        id: int | None,
        business_id: int,
        name: str,
        recipe_type: RecipeType,
    ) -> None:
        if id is not None and (
            isinstance(id, bool) or not isinstance(id, int) or id <= 0
        ):
            raise InvalidRecipe("Recipe ID must be a positive integer or None.")
        if (
            isinstance(business_id, bool)
            or not isinstance(business_id, int)
            or business_id <= 0
        ):
            raise InvalidRecipe("Business ID must be a positive integer.")
        if not isinstance(name, str) or not name.strip():
            raise InvalidRecipe("Recipe name is required.")
        if not isinstance(recipe_type, RecipeType):
            raise InvalidRecipe("Recipe type is invalid.")
        self._id = id
        self._business_id = business_id
        self._name = name.strip()
        self._recipe_type = recipe_type
        self._inputs: list[RecipeInput] = []
        self._outputs: list[RecipeOutput] = []
        self._input_ingredients: dict[int, Ingredient] = {}
        self._output_ingredients: dict[int, Ingredient] = {}

    @property
    def id(self) -> int | None:
        return self._id

    @property
    def business_id(self) -> int:
        return self._business_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def recipe_type(self) -> RecipeType:
        return self._recipe_type

    @property
    def inputs(self) -> tuple[RecipeInput, ...]:
        return tuple(self._inputs)

    @property
    def outputs(self) -> tuple[RecipeOutput, ...]:
        return tuple(self._outputs)

    def add_input(
        self,
        ingredient: Ingredient,
        quantity: Quantity,
        notes: str | None = None,
    ) -> RecipeInput:
        self._validate_ingredient(ingredient)
        line = RecipeInput.for_ingredient(ingredient, quantity, notes)
        if line.ingredient_id in self._input_ingredients:
            raise InvalidRecipe("An Ingredient can appear only once in Recipe inputs.")
        self._inputs.append(line)
        self._input_ingredients[line.ingredient_id] = ingredient
        return line

    def add_output(
        self,
        ingredient: Ingredient,
        quantity: Quantity,
        *,
        is_primary: bool = False,
        notes: str | None = None,
    ) -> RecipeOutput:
        self._validate_ingredient(ingredient)
        line = RecipeOutput.for_ingredient(
            ingredient,
            quantity,
            is_primary=is_primary,
            notes=notes,
        )
        if line.ingredient_id in self._output_ingredients:
            raise InvalidRecipe("An Ingredient can appear only once in Recipe outputs.")
        if is_primary and any(output.is_primary for output in self._outputs):
            raise InvalidRecipe("A Recipe can have at most one primary output.")
        self._outputs.append(line)
        self._output_ingredients[line.ingredient_id] = ingredient
        return line

    def _validate_ingredient(self, ingredient: Ingredient) -> None:
        if not isinstance(ingredient, Ingredient) or ingredient.id is None:
            raise InvalidRecipe("Recipe lines require an identified Ingredient.")
        if ingredient.business_id != self.business_id:
            raise TenantMismatch("Recipe and Ingredient must belong to one Business.")
