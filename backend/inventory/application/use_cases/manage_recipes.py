from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from inventory.application.dto.recipe import RecipeDTO, RecipePageDTO
from inventory.application.ports.recipe_repositories import RecipeRepository, RecipeUnitOfWork
from inventory.domain.entities.ingredient import Ingredient
from inventory.domain.entities.recipe import Recipe
from inventory.domain.entities.recipe_input import RecipeInput
from inventory.domain.entities.recipe_output import RecipeOutput
from inventory.domain.enums.recipe import RecipeType
from inventory.domain.value_objects.quantity import Quantity
from inventory.domain.value_objects.unit import Unit


class RecipeNotFound(Exception):
    pass


class RecipeIngredientNotFound(Exception):
    pass


class InactiveRecipeIngredient(Exception):
    pass


@dataclass(frozen=True, slots=True)
class RecipeLineCommand:
    ingredient_id: int
    quantity: Decimal
    unit: str
    notes: str | None = None
    is_primary: bool = False


class ManageRecipes:
    MAX_PAGE_SIZE = 100

    def __init__(self, recipes: RecipeRepository, unit_of_work: RecipeUnitOfWork):
        self._recipes = recipes
        self._unit_of_work = unit_of_work

    def list(self, business_id: int, *, page: int, page_size: int,
             search: str | None = None, recipe_type: str | None = None,
             is_active: bool | None = None) -> RecipePageDTO:
        self._positive_id(business_id, "Business ID")
        if page < 1 or page_size < 1 or page_size > self.MAX_PAGE_SIZE:
            raise ValueError("Page must be positive and page_size must be between 1 and 100.")
        return self._recipes.list_for_business(
            business_id, page=page, page_size=page_size, search=search,
            recipe_type=recipe_type, is_active=is_active,
        )

    def get(self, business_id: int, recipe_id: int) -> RecipeDTO:
        self._positive_id(business_id, "Business ID")
        self._positive_id(recipe_id, "Recipe ID")
        recipe = self._recipes.get_for_business(business_id, recipe_id)
        if recipe is None:
            raise RecipeNotFound("Recipe does not exist in this business.")
        return recipe

    def create(self, business_id: int, *, name: str, recipe_type: str,
               code: str | None, description: str | None, is_active: bool,
               inputs: list[RecipeLineCommand], outputs: list[RecipeLineCommand]) -> RecipeDTO:
        self._positive_id(business_id, "Business ID")
        recipe = Recipe(None, business_id, name, RecipeType(recipe_type))
        with self._unit_of_work.atomic():
            input_lines = [self._make_line(recipe, row, "input") for row in inputs]
            output_lines = [self._make_line(recipe, row, "output") for row in outputs]
            return self._recipes.create(
                recipe, code=code, description=description, is_active=is_active,
                inputs=input_lines, outputs=output_lines,
            )

    def update(self, business_id: int, recipe_id: int, **changes) -> RecipeDTO:
        with self._unit_of_work.atomic():
            current = self._recipes.get_for_business(business_id, recipe_id, lock=True)
            if current is None:
                raise RecipeNotFound("Recipe does not exist in this business.")
            recipe = Recipe(
                current.id, business_id,
                changes.get("name", current.name),
                RecipeType(changes.get("type", current.type)),
            )
            updated = self._recipes.update_header(
                business_id, recipe_id, recipe,
                code=changes.get("code", current.code),
                description=changes.get("description", current.description),
                is_active=changes.get("is_active", current.is_active),
            )
            if updated is not None and ("inputs" in changes or "outputs" in changes):
                aggregate = Recipe(
                    current.id, business_id, recipe.name, recipe.recipe_type,
                )
                for kind, field in (("input", "inputs"), ("output", "outputs")):
                    if field not in changes:
                        continue
                    lines = [
                        self._make_line(aggregate, command, kind)
                        for command in changes[field]
                    ]
                    if not self._recipes.replace_lines(
                        business_id, recipe_id, kind, lines,
                    ):
                        raise RecipeNotFound("Recipe does not exist in this business.")
                updated = self._recipes.get_for_business(business_id, recipe_id, lock=True)
        if updated is None:
            raise RecipeNotFound("Recipe does not exist in this business.")
        return updated

    def add_line(self, business_id: int, recipe_id: int, kind: str,
                 command: RecipeLineCommand) -> RecipeDTO:
        self._validate_kind(kind)
        with self._unit_of_work.atomic():
            recipe_data = self._recipes.get_for_business(business_id, recipe_id, lock=True)
            if recipe_data is None:
                raise RecipeNotFound("Recipe does not exist in this business.")
            aggregate = self._aggregate(recipe_data, business_id)
            line = self._make_line(aggregate, command, kind)
            result = self._recipes.save_line(business_id, recipe_id, kind, line)
        if result is None:
            raise RecipeNotFound("Recipe does not exist in this business.")
        return result

    def update_line(self, business_id: int, recipe_id: int, kind: str,
                    line_id: int, command: RecipeLineCommand) -> RecipeDTO:
        self._validate_kind(kind)
        with self._unit_of_work.atomic():
            recipe_data = self._recipes.get_for_business(business_id, recipe_id, lock=True)
            if recipe_data is None:
                raise RecipeNotFound("Recipe does not exist in this business.")
            rows = recipe_data.inputs if kind == "input" else recipe_data.outputs
            target = next((row for row in rows if row.id == line_id), None)
            if target is None:
                raise RecipeNotFound("Recipe line does not exist in this business.")
            aggregate = self._aggregate(
                recipe_data, business_id,
                excluded=(kind, line_id),
            )
            line = self._make_line(aggregate, command, kind)
            result = self._recipes.save_line(
                business_id, recipe_id, kind, line, line_id=line_id,
            )
        if result is None:
            raise RecipeNotFound("Recipe line does not exist in this business.")
        return result

    def patch_line(self, business_id: int, recipe_id: int, kind: str,
                   line_id: int, changes: dict) -> RecipeDTO:
        self._validate_kind(kind)
        with self._unit_of_work.atomic():
            recipe_data = self._recipes.get_for_business(business_id, recipe_id, lock=True)
            if recipe_data is None:
                raise RecipeNotFound("Recipe does not exist in this business.")
            rows = recipe_data.inputs if kind == "input" else recipe_data.outputs
            current = next((row for row in rows if row.id == line_id), None)
            if current is None:
                raise RecipeNotFound("Recipe line does not exist in this business.")
            command = RecipeLineCommand(
                ingredient_id=changes.get("ingredient_id", current.ingredient_id),
                quantity=changes.get("quantity", current.quantity),
                unit=changes.get("unit", current.unit),
                notes=changes.get("notes", current.notes),
                is_primary=(
                    changes.get("is_primary", current.is_primary)
                    if kind == "output" else False
                ),
            )
            aggregate = self._aggregate(recipe_data, business_id, excluded=(kind, line_id))
            line = self._make_line(aggregate, command, kind)
            result = self._recipes.save_line(
                business_id, recipe_id, kind, line, line_id=line_id,
            )
        if result is None:
            raise RecipeNotFound("Recipe line does not exist in this business.")
        return result

    def delete_line(self, business_id: int, recipe_id: int, kind: str, line_id: int) -> None:
        self._validate_kind(kind)
        with self._unit_of_work.atomic():
            if self._recipes.get_for_business(business_id, recipe_id, lock=True) is None:
                raise RecipeNotFound("Recipe does not exist in this business.")
            if not self._recipes.delete_line(business_id, recipe_id, kind, line_id):
                raise RecipeNotFound("Recipe line does not exist in this business.")

    def _make_line(self, recipe: Recipe, command: RecipeLineCommand, kind: str):
        self._positive_id(command.ingredient_id, "Ingredient ID")
        ingredient = self._recipes.get_ingredient_for_update(
            recipe.business_id, command.ingredient_id,
        )
        if ingredient is None:
            raise RecipeIngredientNotFound("Ingredient does not exist in this business.")
        if not ingredient.is_active:
            raise InactiveRecipeIngredient("Inactive ingredients cannot be added to a recipe.")
        quantity = Quantity(command.quantity, Unit(command.unit))
        if kind == "input":
            return recipe.add_input(ingredient, quantity, command.notes)
        return recipe.add_output(
            ingredient, quantity, is_primary=command.is_primary, notes=command.notes,
        )

    def _aggregate(self, data: RecipeDTO, business_id: int,
                   excluded: tuple[str, int] | None = None) -> Recipe:
        aggregate = Recipe(data.id, business_id, data.name, RecipeType(data.type))
        for kind, rows in (("input", data.inputs), ("output", data.outputs)):
            for row in rows:
                if excluded == (kind, row.id):
                    continue
                ingredient = self._recipes.get_ingredient_for_update(
                    business_id, row.ingredient_id,
                )
                if ingredient is None:
                    raise RecipeIngredientNotFound("Ingredient does not exist in this business.")
                quantity = Quantity(row.quantity, Unit(row.unit))
                if kind == "input":
                    aggregate.add_input(ingredient, quantity, row.notes)
                else:
                    aggregate.add_output(
                        ingredient, quantity, is_primary=row.is_primary, notes=row.notes,
                    )
        return aggregate

    @staticmethod
    def _validate_kind(kind: str) -> None:
        if kind not in ("input", "output"):
            raise ValueError("Recipe line kind must be input or output.")

    @staticmethod
    def _positive_id(value: int, label: str) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{label} must be a positive integer.")
