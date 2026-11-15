from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Event, local
from time import monotonic
from uuid import uuid4

from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase, skipUnlessDBFeature

from accounts.models import Business
from inventory.application.use_cases.manage_recipes import ManageRecipes, RecipeLineCommand
from inventory.infrastructure.django.recipe_repository import DjangoRecipeRepository
from inventory.infrastructure.django.unit_of_work import DjangoInventoryUnitOfWork
from inventory.models import Ingredient


@skipUnlessDBFeature("has_select_for_update")
class RecipePostgreSQLConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        if connection.vendor != "postgresql":
            self.skipTest("Recipe lock-order tests require PostgreSQL row locks.")
        self.business = Business.objects.create(name="Recipe lock ordering")
        self.flour = Ingredient.objects.create(
            business=self.business, name="Flour", unit="kg", preparation_level="raw"
        )
        self.sugar = Ingredient.objects.create(
            business=self.business, name="Sugar", unit="kg", preparation_level="raw"
        )

    def test_concurrent_multiline_recipe_creation_with_reversed_input_order_does_not_deadlock(self):
        first_locked = Event()
        release_first = Event()
        worker_state = local()
        delegate = DjangoRecipeRepository()
        self_outer = self

        class HoldingRepository:
            def __getattr__(self, name):
                return getattr(delegate, name)

            def get_ingredient_for_update(self, business_id, ingredient_id):
                result = delegate.get_ingredient_for_update(business_id, ingredient_id)
                if worker_state.role == "first" and ingredient_id == min(
                    self_outer.flour.pk, self_outer.sugar.pk
                ):
                    first_locked.set()
                    if not release_first.wait(15):
                        raise TimeoutError("test coordinator did not release first recipe")
                return result

        manager = ManageRecipes(HoldingRepository(), DjangoInventoryUnitOfWork())
        prefix = f"recipe_lock_order_{uuid4().hex[:8]}"

        def create_recipe(role, label, ingredient_ids):
            close_old_connections()
            worker_state.role = role
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute("SET application_name = %s", [label])
                lines = [
                    RecipeLineCommand(
                        ingredient_id=ingredient_id,
                        quantity=Decimal("1"),
                        unit="kg",
                    )
                    for ingredient_id in ingredient_ids
                ]
                return manager.create(
                    self.business.pk,
                    name=f"Concurrent recipe {role}",
                    recipe_type="preparation",
                    code=None,
                    description=None,
                    is_active=True,
                    inputs=lines,
                    outputs=[],
                ), None
            except Exception as error:
                return None, error
            finally:
                connections.close_all()

        def wait_until_blocked(label):
            deadline = monotonic() + 15
            while monotonic() < deadline:
                with connections["default"].cursor() as cursor:
                    cursor.execute(
                        """SELECT wait_event_type, cardinality(pg_blocking_pids(pid))
                           FROM pg_stat_activity WHERE application_name = %s""",
                        [label],
                    )
                    row = cursor.fetchone()
                if row and row[0] == "Lock" and row[1] > 0:
                    return
            self.fail(f"PostgreSQL did not report a lock wait for {label}.")

        ordered = sorted((self.flour.pk, self.sugar.pk))
        with ThreadPoolExecutor(max_workers=2) as pool:
            first_future = pool.submit(
                create_recipe, "first", f"{prefix}_first", ordered
            )
            try:
                self.assertTrue(
                    first_locked.wait(10),
                    "first recipe did not acquire its first Ingredient lock",
                )
                second_future = pool.submit(
                    create_recipe, "second", f"{prefix}_second", list(reversed(ordered))
                )
                wait_until_blocked(f"{prefix}_second")
            finally:
                release_first.set()
            first_result = first_future.result(timeout=20)
            second_result = second_future.result(timeout=20)

        self.assertIsNone(first_result[1], repr(first_result[1]))
        self.assertIsNone(second_result[1], repr(second_result[1]))
        self.assertEqual(len(first_result[0].inputs), 2)
        self.assertEqual(len(second_result[0].inputs), 2)


    def test_concurrent_recipe_replacements_lock_existing_and_new_ingredients_in_one_global_order(self):
        first_locked = Event()
        release_first = Event()
        worker_state = local()
        delegate = DjangoRecipeRepository()
        self_outer = self

        class HoldingRepository:
            def __getattr__(self, name):
                return getattr(delegate, name)

            def get_ingredient_for_update(self, business_id, ingredient_id):
                result = delegate.get_ingredient_for_update(business_id, ingredient_id)
                if worker_state.role == "first" and ingredient_id == min(
                    self_outer.flour.pk, self_outer.sugar.pk
                ):
                    first_locked.set()
                    if not release_first.wait(15):
                        raise TimeoutError("test coordinator did not release first recipe")
                return result

        base_manager = ManageRecipes(delegate, DjangoInventoryUnitOfWork())
        first_recipe = base_manager.create(
            self.business.pk, name="First replacement recipe", recipe_type="preparation",
            code=None, description=None, is_active=True,
            inputs=[RecipeLineCommand(self.flour.pk, Decimal("1"), "kg")], outputs=[],
        )
        second_recipe = base_manager.create(
            self.business.pk, name="Second replacement recipe", recipe_type="preparation",
            code=None, description=None, is_active=True,
            inputs=[RecipeLineCommand(self.sugar.pk, Decimal("1"), "kg")], outputs=[],
        )
        manager = ManageRecipes(HoldingRepository(), DjangoInventoryUnitOfWork())
        prefix = f"recipe_replace_order_{uuid4().hex[:8]}"

        def replace_recipe(role, label, recipe_id, ingredient_id):
            close_old_connections()
            worker_state.role = role
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute("SET application_name = %s", [label])
                result = manager.update(
                    self.business.pk, recipe_id,
                    inputs=[RecipeLineCommand(ingredient_id, Decimal("1"), "kg")],
                )
                return result, None
            except Exception as error:
                return None, error
            finally:
                connections.close_all()

        def wait_until_blocked(label):
            deadline = monotonic() + 15
            while monotonic() < deadline:
                with connections["default"].cursor() as cursor:
                    cursor.execute(
                        """SELECT wait_event_type, cardinality(pg_blocking_pids(pid))
                           FROM pg_stat_activity WHERE application_name = %s""",
                        [label],
                    )
                    row = cursor.fetchone()
                if row and row[0] == "Lock" and row[1] > 0:
                    return
            self.fail(f"PostgreSQL did not report a lock wait for {label}.")

        with ThreadPoolExecutor(max_workers=2) as pool:
            first_future = pool.submit(
                replace_recipe, "first", f"{prefix}_first",
                first_recipe.id, self.sugar.pk,
            )
            try:
                self.assertTrue(
                    first_locked.wait(10),
                    "first replacement did not acquire the globally first Ingredient lock",
                )
                second_future = pool.submit(
                    replace_recipe, "second", f"{prefix}_second",
                    second_recipe.id, self.flour.pk,
                )
                wait_until_blocked(f"{prefix}_second")
            finally:
                release_first.set()
            first_result = first_future.result(timeout=20)
            second_result = second_future.result(timeout=20)

        self.assertIsNone(first_result[1], repr(first_result[1]))
        self.assertIsNone(second_result[1], repr(second_result[1]))
        self.assertEqual([line.ingredient_id for line in first_result[0].inputs], [self.sugar.pk])
        self.assertEqual([line.ingredient_id for line in second_result[0].inputs], [self.flour.pk])
