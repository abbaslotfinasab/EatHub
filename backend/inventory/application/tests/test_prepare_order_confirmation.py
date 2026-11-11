from contextlib import nullcontext
from types import SimpleNamespace
from unittest import TestCase

from inventory.application.context import InventoryExecutionContext
from inventory.application.exceptions import OperationConflict, ResourceNotFound
from inventory.application.use_cases.prepare_order_confirmation import PrepareOrderConfirmation


class FakeRecipes:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def get_for_business(self, business_id, recipe_id, *, lock=False):
        self.calls.append((business_id, recipe_id, lock))
        row = self.rows.get(recipe_id)
        return row if row and row.business_id == business_id else None


class FakeWarehouses:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def get_active_defaults_for_business(self, business_id, *, lock=False):
        self.calls.append((business_id, lock))
        return self.rows


class PrepareOrderConfirmationTests(TestCase):
    def setUp(self):
        self.context = InventoryExecutionContext(7, 11)
        self.line = SimpleNamespace(
            ingredient_business_id=7,
            ingredient_is_active=True,
            ingredient_unit="kg",
        )
        self.recipe = SimpleNamespace(
            id=31, business_id=7, name="Soup", is_active=True,
            inputs=(self.line,), outputs=(),
        )
        self.recipes = FakeRecipes({31: self.recipe})
        self.warehouses = FakeWarehouses([SimpleNamespace(id=41)])
        self.use_case = PrepareOrderConfirmation(
            self.recipes, self.warehouses, SimpleNamespace(atomic=lambda: nullcontext())
        )

    def test_returns_scoped_recipe_and_locks_warehouse_and_recipe(self):
        result = self.use_case.execute(self.context, [31, 31])

        self.assertEqual(result.warehouse_id, 41)
        self.assertEqual(result.recipes, (self.recipe,))
        self.assertEqual(self.warehouses.calls, [(7, True)])
        self.assertEqual(self.recipes.calls, [(7, 31, True)])

    def test_rejects_missing_or_ambiguous_default_warehouse(self):
        self.warehouses.rows = []
        with self.assertRaises(OperationConflict):
            self.use_case.execute(self.context, [31])
        self.warehouses.rows = [SimpleNamespace(id=41), SimpleNamespace(id=42)]
        with self.assertRaises(OperationConflict):
            self.use_case.execute(self.context, [31])

    def test_rejects_recipe_from_another_business(self):
        self.recipes.rows[31] = SimpleNamespace(
            id=31, business_id=8, name="Foreign", is_active=True, inputs=(), outputs=()
        )
        with self.assertRaises(ResourceNotFound):
            self.use_case.execute(self.context, [31])

    def test_rejects_inactive_or_cross_business_ingredients(self):
        self.line.ingredient_is_active = False
        with self.assertRaises(OperationConflict):
            self.use_case.execute(self.context, [31])
        self.line.ingredient_is_active = True
        self.line.ingredient_business_id = 8
        with self.assertRaises(OperationConflict):
            self.use_case.execute(self.context, [31])
