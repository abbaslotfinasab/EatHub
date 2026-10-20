from decimal import Decimal
from unittest import TestCase

from inventory.domain.entities.ingredient import Ingredient
from inventory.domain.entities.recipe import Recipe
from inventory.domain.enums.recipe import RecipeType
from inventory.domain.exceptions import InvalidRecipe, TenantMismatch
from inventory.domain.value_objects.quantity import Quantity
from inventory.domain.value_objects.unit import Unit


class RecipeTests(TestCase):
    def setUp(self) -> None:
        self.recipe = Recipe(None, 1, "Dough", RecipeType.PREPARATION)
        self.flour = Ingredient(10, 1, "Flour", Unit.KG)
        self.water = Ingredient(11, 1, "Water", Unit.L)

    def test_adds_same_business_inputs_and_outputs(self) -> None:
        input_line = self.recipe.add_input(
            self.flour,
            Quantity(Decimal("500"), Unit.G),
        )
        output_line = self.recipe.add_output(
            self.water,
            Quantity(Decimal("1"), Unit.L),
            is_primary=True,
        )
        self.assertEqual(input_line.quantity, Quantity(Decimal("0.500"), Unit.KG))
        self.assertEqual(output_line.quantity, Quantity(Decimal("1"), Unit.L))
        self.assertEqual(self.recipe.inputs, (input_line,))
        self.assertEqual(self.recipe.outputs, (output_line,))

    def test_rejects_cross_business_ingredient(self) -> None:
        foreign = Ingredient(12, 2, "Rice", Unit.KG)
        with self.assertRaises(TenantMismatch):
            self.recipe.add_input(foreign, Quantity(Decimal("1"), Unit.KG))

    def test_rejects_duplicate_ingredient_lines(self) -> None:
        self.recipe.add_input(self.flour, Quantity(Decimal("1"), Unit.KG))
        with self.assertRaises(InvalidRecipe):
            self.recipe.add_input(self.flour, Quantity(Decimal("2"), Unit.KG))
        self.recipe.add_output(self.flour, Quantity(Decimal("1"), Unit.KG))
        with self.assertRaises(InvalidRecipe):
            self.recipe.add_output(self.flour, Quantity(Decimal("2"), Unit.KG))

    def test_allows_at_most_one_primary_output(self) -> None:
        self.recipe.add_output(
            self.flour,
            Quantity(Decimal("1"), Unit.KG),
            is_primary=True,
        )
        with self.assertRaises(InvalidRecipe):
            self.recipe.add_output(
                self.water,
                Quantity(Decimal("1"), Unit.L),
                is_primary=True,
            )

    def test_rejects_non_positive_line_quantity(self) -> None:
        with self.assertRaises(InvalidRecipe):
            self.recipe.add_input(self.flour, Quantity.zero(Unit.KG))

    def test_child_collections_are_read_only_views(self) -> None:
        self.recipe.add_input(self.flour, Quantity(Decimal("1"), Unit.KG))
        with self.assertRaises(AttributeError):
            self.recipe.inputs.append("invalid")
