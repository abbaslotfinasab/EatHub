from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Event, local
from time import monotonic
from uuid import uuid4

from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase, skipUnlessDBFeature

from accounts.models import Business
from inventory.application.use_cases.manage_recipes import ManageRecipes, RecipeLineCommand
from inventory.infrastructure.django.compound_material_repository import DjangoCompoundMaterialRepository
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

    def test_concurrent_cross_recipe_line_mutations_lock_existing_and_new_ingredients_together(self):
        ordered = sorted((self.flour.pk, self.sugar.pk))
        first_recipe = self._create_single_ingredient_recipe(ordered[0], "First")
        second_recipe = self._create_single_ingredient_recipe(ordered[1], "Second")

        first_locked = Event()
        release_first = Event()
        worker_state = local()
        delegate = DjangoRecipeRepository()
        flour_id = self.flour.pk

        class CoordinatedRepository:
            def __getattr__(self, name):
                return getattr(delegate, name)

            def get_ingredient_for_update(self, business_id, ingredient_id):
                result = delegate.get_ingredient_for_update(business_id, ingredient_id)
                if worker_state.role == "first" and ingredient_id == ordered[0]:
                    first_locked.set()
                    if not release_first.wait(15):
                        raise TimeoutError("test coordinator did not release first recipe")
                return result

        manager = ManageRecipes(CoordinatedRepository(), DjangoInventoryUnitOfWork())
        prefix = f"recipe_cross_add_{uuid4().hex[:8]}"

        def mutate_line(role, label, recipe_id, ingredient_id, line_id=None):
            close_old_connections()
            worker_state.role = role
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute("SET application_name = %s", [label])
                command = RecipeLineCommand(
                    ingredient_id=ingredient_id,
                    quantity=Decimal("1"),
                    unit="kg",
                )
                if line_id is None:
                    result = manager.add_line(self.business.pk, recipe_id, "input", command)
                else:
                    result = manager.update_line(
                        self.business.pk, recipe_id, "input", line_id, command,
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
                mutate_line, "first", f"{prefix}_first", first_recipe.id, ordered[1]
            )
            try:
                self.assertTrue(
                    first_locked.wait(10),
                    "first mutation did not acquire the lowest Ingredient lock",
                )
                second_future = pool.submit(
                    mutate_line, "second", f"{prefix}_second", second_recipe.id,
                    ordered[0], second_recipe.inputs[0].id
                )
                wait_until_blocked(f"{prefix}_second")
            finally:
                release_first.set()
            first_result = first_future.result(timeout=20)
            second_result = second_future.result(timeout=20)

        self.assertIsNone(first_result[1], repr(first_result[1]))
        self.assertIsNone(second_result[1], repr(second_result[1]))
        self.assertEqual(len(first_result[0].inputs), 2)
        self.assertEqual(len(second_result[0].inputs), 1)
        self.assertEqual(second_result[0].inputs[0].id, second_recipe.inputs[0].id)

    def _create_single_ingredient_recipe(self, ingredient_id, label):
        manager = ManageRecipes(DjangoRecipeRepository(), DjangoInventoryUnitOfWork())
        return manager.create(
            self.business.pk,
            name=f"{label} recipe",
            recipe_type="preparation",
            code=None,
            description=None,
            is_active=True,
            inputs=[
                RecipeLineCommand(
                    ingredient_id=ingredient_id,
                    quantity=Decimal("1"),
                    unit="kg",
                )
            ],
            outputs=[],
        )


    def test_compound_component_update_uses_global_lock_order_with_recipe_mutation(self):
        compound_repository = DjangoCompoundMaterialRepository()
        compound = compound_repository.create(
            self.business.pk,
            {
                "name": "Prepared flour mix",
                "unit": "kg",
                "components": [
                    {"ingredient_id": self.flour.pk, "quantity": Decimal("1"), "unit": "kg"},
                    {"ingredient_id": self.sugar.pk, "quantity": Decimal("1"), "unit": "kg"},
                ],
            },
        )
        recipe_manager = ManageRecipes(DjangoRecipeRepository(), DjangoInventoryUnitOfWork())
        recipe = recipe_manager.create(
            self.business.pk,
            name="Compound and raw ingredient",
            recipe_type="preparation",
            code=None,
            description=None,
            is_active=True,
            inputs=[
                RecipeLineCommand(self.flour.pk, Decimal("1"), "kg"),
                RecipeLineCommand(compound.id, Decimal("1"), "kg"),
            ],
            outputs=[],
        )

        first_locked = Event()
        release_first = Event()
        worker_state = local()
        delegate = DjangoRecipeRepository()
        flour_id = self.flour.pk

        class CoordinatedRepository:
            def __getattr__(self, name):
                return getattr(delegate, name)

            def get_ingredient_for_update(self, business_id, ingredient_id):
                result = delegate.get_ingredient_for_update(business_id, ingredient_id)
                if worker_state.role == "recipe" and ingredient_id == flour_id:
                    first_locked.set()
                    if not release_first.wait(15):
                        raise TimeoutError("test coordinator did not release Recipe mutation")
                return result

        manager = ManageRecipes(CoordinatedRepository(), DjangoInventoryUnitOfWork())
        prefix = f"recipe_compound_order_{uuid4().hex[:8]}"

        def mutate_recipe():
            close_old_connections()
            worker_state.role = "recipe"
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute("SET application_name = %s", [f"{prefix}_recipe"])
                return manager.add_line(
                    self.business.pk,
                    recipe.id,
                    "input",
                    RecipeLineCommand(self.sugar.pk, Decimal("1"), "kg"),
                ), None
            except Exception as error:
                return None, error
            finally:
                connections.close_all()

        def update_compound():
            close_old_connections()
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute("SET application_name = %s", [f"{prefix}_compound"])
                return compound_repository.update(
                    self.business.pk,
                    compound.id,
                    {
                        "components": [
                            {"ingredient_id": self.flour.pk, "quantity": Decimal("1"), "unit": "kg"},
                            {"ingredient_id": self.sugar.pk, "quantity": Decimal("1"), "unit": "kg"},
                        ],
                    },
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

        with ThreadPoolExecutor(max_workers=2) as pool:
            recipe_future = pool.submit(mutate_recipe)
            try:
                self.assertTrue(
                    first_locked.wait(10),
                    "Recipe mutation did not acquire its first Ingredient lock",
                )
                compound_future = pool.submit(update_compound)
                wait_until_blocked(f"{prefix}_compound")
            finally:
                release_first.set()
            recipe_result = recipe_future.result(timeout=20)
            compound_result = compound_future.result(timeout=20)

        self.assertIsNone(recipe_result[1], repr(recipe_result[1]))
        self.assertIsNone(compound_result[1], repr(compound_result[1]))
        self.assertEqual(len(recipe_result[0].inputs), 3)
        self.assertEqual(len(compound_result[0].components), 2)
