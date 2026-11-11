from unittest import TestCase
from types import SimpleNamespace

from inventory.application.exceptions import InvalidApplicationInput, ResourceNotFound
from inventory.application.use_cases.resolve_order_requirement_ingredients import ResolveOrderRequirementIngredients
from inventory.domain.value_objects.unit import Unit


class FakeIngredients:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def get_many_for_business(self, ingredient_ids, business_id):
        self.calls.append((tuple(ingredient_ids), business_id))
        return [
            self.rows[ingredient_id]
            for ingredient_id in ingredient_ids
            if ingredient_id in self.rows and self.rows[ingredient_id].business_id == business_id
        ]


class ResolveOrderRequirementIngredientsTests(TestCase):
    def setUp(self):
        self.ingredients = FakeIngredients({
            4: SimpleNamespace(id=4, business_id=7, name="Flour", canonical_unit=Unit("kg")),
            9: SimpleNamespace(id=9, business_id=7, name="Water", canonical_unit=Unit("l")),
        })
        self.use_case = ResolveOrderRequirementIngredients(self.ingredients)

    def test_resolves_unique_ids_in_deterministic_order(self):
        result = self.use_case.execute(business_id=7, ingredient_ids=[9, 4, 9])
        self.assertEqual([row.id for row in result], [4, 9])
        self.assertEqual(self.ingredients.calls, [((4, 9), 7)])
        self.assertEqual(result[0].name, "Flour")
        self.assertEqual(result[0].canonical_unit, "kg")

    def test_rejects_foreign_or_missing_ingredient(self):
        with self.assertRaises(ResourceNotFound):
            self.use_case.execute(business_id=8, ingredient_ids=[4])

    def test_rejects_invalid_input(self):
        with self.assertRaises(InvalidApplicationInput):
            self.use_case.execute(business_id=7, ingredient_ids=[])
        with self.assertRaises(InvalidApplicationInput):
            self.use_case.execute(business_id=7, ingredient_ids=[True])
