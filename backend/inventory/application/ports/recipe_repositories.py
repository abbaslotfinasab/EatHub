from typing import Protocol

from inventory.application.dto.recipe import RecipeDTO, RecipePageDTO
from inventory.domain.entities.ingredient import Ingredient
from inventory.domain.entities.recipe import Recipe
from inventory.domain.entities.recipe_input import RecipeInput
from inventory.domain.entities.recipe_output import RecipeOutput


class RecipeRepository(Protocol):
    def list_for_business(
        self, business_id: int, *, page: int, page_size: int,
        search: str | None, recipe_type: str | None, is_active: bool | None,
    ) -> RecipePageDTO: ...

    def get_for_business(
        self, business_id: int, recipe_id: int, *, lock: bool = False,
    ) -> RecipeDTO | None: ...

    def create(
        self, recipe: Recipe, *, code: str | None, description: str | None,
        is_active: bool, inputs: list[RecipeInput], outputs: list[RecipeOutput],
    ) -> RecipeDTO: ...

    def update_header(
        self, business_id: int, recipe_id: int, recipe: Recipe, *,
        code: str | None, description: str | None, is_active: bool,
    ) -> RecipeDTO | None: ...

    def replace_lines(
        self, business_id: int, recipe_id: int, kind: str,
        lines: list[RecipeInput] | list[RecipeOutput],
    ) -> bool: ...

    def save_line(
        self, business_id: int, recipe_id: int, kind: str,
        line: RecipeInput | RecipeOutput, line_id: int | None = None,
    ) -> RecipeDTO | None: ...

    def delete_line(
        self, business_id: int, recipe_id: int, kind: str, line_id: int,
    ) -> bool: ...

    def get_ingredient_for_update(
        self, business_id: int, ingredient_id: int,
    ) -> Ingredient | None: ...


class RecipeUnitOfWork(Protocol):
    def atomic(self): ...
