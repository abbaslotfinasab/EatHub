from decimal import Decimal
from importlib import import_module
from unittest import skipUnless
from unittest.mock import Mock

from django.db import DatabaseError, connection
from django.db.migrations.executor import MigrationExecutor
from django.test import SimpleTestCase, TransactionTestCase


class InventoryMasterDataMigrationGraphTests(SimpleTestCase):
    def test_master_data_constraints_follow_permission_seed_migration(self):
        migration = import_module(
            "inventory.migrations.0006_master_data_invariants"
        ).Migration

        self.assertIn(
            ("accounts", "0010_inventory_master_permissions"),
            migration.dependencies,
        )
        self.assertIn(
            ("inventory", "0005_retire_legacy_purchase_models_state"),
            migration.dependencies,
        )


class InventoryTenantMigrationInstallTests(SimpleTestCase):
    def _postgres_schema_editor(self):
        schema_editor = Mock()
        schema_editor.connection.vendor = "postgresql"
        return schema_editor

    def test_0018_preflight_precedes_function_and_trigger_creation(self):
        migration = import_module(
            "inventory.migrations.0018_inventory_tenant_integrity_guards"
        )
        schema_editor = self._postgres_schema_editor()

        migration.install_tenant_integrity_guards(None, schema_editor)

        calls = schema_editor.execute.call_args_list
        self.assertEqual(calls[0].args[0], migration.VALIDATE_EXISTING_SQL)
        self.assertEqual(calls[1].args[0], migration.CREATE_FUNCTION_SQL)
        self.assertEqual(len(calls), 8)

    def test_0018_preflight_failure_stops_before_installing_guards(self):
        migration = import_module(
            "inventory.migrations.0018_inventory_tenant_integrity_guards"
        )
        schema_editor = self._postgres_schema_editor()
        schema_editor.execute.side_effect = RuntimeError("preflight rejected data")

        with self.assertRaisesRegex(RuntimeError, "preflight rejected data"):
            migration.install_tenant_integrity_guards(None, schema_editor)

        schema_editor.execute.assert_called_once_with(migration.VALIDATE_EXISTING_SQL)

    def test_0019_preflight_precedes_function_and_trigger_creation(self):
        migration = import_module(
            "inventory.migrations.0019_inventory_legacy_tenant_integrity_guards"
        )
        schema_editor = self._postgres_schema_editor()

        migration.install_legacy_tenant_guards(None, schema_editor)

        calls = schema_editor.execute.call_args_list
        self.assertEqual(calls[0].args[0], migration.PREFLIGHT_SQL)
        self.assertEqual(calls[1].args[0], migration.GUARD_FUNCTION_SQL)
        self.assertEqual(
            len(calls),
            2 + len(migration.CHILD_TABLES) + len(migration.PARENT_TABLES),
        )

    def test_0019_preflight_failure_stops_before_installing_guards(self):
        migration = import_module(
            "inventory.migrations.0019_inventory_legacy_tenant_integrity_guards"
        )
        schema_editor = self._postgres_schema_editor()
        schema_editor.execute.side_effect = RuntimeError("preflight rejected data")

        with self.assertRaisesRegex(RuntimeError, "preflight rejected data"):
            migration.install_legacy_tenant_guards(None, schema_editor)

        schema_editor.execute.assert_called_once_with(migration.PREFLIGHT_SQL)

    def test_0018_reverse_drops_all_v1_triggers_and_function(self):
        migration = import_module(
            "inventory.migrations.0018_inventory_tenant_integrity_guards"
        )
        schema_editor = self._postgres_schema_editor()

        migration.remove_tenant_integrity_guards(None, schema_editor)

        statements = [call.args[0] for call in schema_editor.execute.call_args_list]
        self.assertEqual(len(statements), 7)
        for table in (
            "inventory_v1_stock",
            "inventory_v1_stock_movement",
            "inventory_operation",
            "inventory_operation_line",
            "inventory_reservation",
            "inventory_reservation_line",
        ):
            self.assertIn(
                f"DROP TRIGGER IF EXISTS {table}_tenant_integrity ON {table}",
                statements,
            )
        self.assertEqual(
            statements[-1],
            "DROP FUNCTION IF EXISTS inventory_v1_enforce_tenant_integrity()",
        )

    def test_0019_reverse_drops_all_legacy_and_parent_triggers_and_function(self):
        migration = import_module(
            "inventory.migrations.0019_inventory_legacy_tenant_integrity_guards"
        )
        schema_editor = self._postgres_schema_editor()

        migration.remove_legacy_tenant_guards(None, schema_editor)

        statements = [call.args[0] for call in schema_editor.execute.call_args_list]
        self.assertEqual(
            len(statements),
            len(migration.CHILD_TABLES) + len(migration.PARENT_TABLES) + 1,
        )
        for table in migration.CHILD_TABLES:
            self.assertIn(
                f"DROP TRIGGER IF EXISTS {table}_legacy_tenant_integrity ON {table}",
                statements,
            )
        for table in migration.PARENT_TABLES:
            self.assertIn(
                f"DROP TRIGGER IF EXISTS {table}_parent_tenant_integrity ON {table}",
                statements,
            )
        self.assertEqual(
            statements[-1],
            "DROP FUNCTION IF EXISTS inventory_enforce_legacy_tenant_integrity()",
        )


class InventoryTenantMigrationReverseTests(SimpleTestCase):
    def test_0020_reverse_restores_unlocked_v1_and_preexisting_legacy_guards(self):
        migration = import_module(
            "inventory.migrations.0020_inventory_v1_tenant_locking"
        )
        schema_editor = Mock()
        schema_editor.connection.vendor = "postgresql"

        migration.restore_unlocked_tenant_guards(None, schema_editor)

        calls = schema_editor.execute.call_args_list
        self.assertEqual(len(calls), 2)
        v1_function_sql = calls[0].args[0]
        legacy_function_sql = calls[1].args[0]
        self.assertIn(
            "FROM inventory_warehouse WHERE id = NEW.destination_warehouse_id",
            v1_function_sql,
        )
        self.assertNotIn(
            "FROM inventory_warehouse WHERE id = NEW.destination_warehouse_id FOR SHARE",
            v1_function_sql,
        )
        self.assertIn(
            "FROM inventory_warehouse WHERE id = NEW.warehouse_id FOR SHARE",
            legacy_function_sql,
        )
        self.assertIn(
            "FROM inventory_warehouse WHERE id = NEW.destination_warehouse_id",
            legacy_function_sql,
        )
        self.assertNotIn(
            "FROM inventory_warehouse WHERE id = NEW.destination_warehouse_id FOR SHARE",
            legacy_function_sql,
        )


@skipUnless(connection.vendor == "postgresql", "Migration preflight requires PostgreSQL")
class InventoryTenantMigrationExecutorPreflightTests(TransactionTestCase):
    """Exercise the real PostgreSQL preflight SQL against historical database states."""

    reset_sequences = True

    inventory_0017 = ("inventory", "0017_inventory_stock_movement_append_only")
    inventory_0018 = ("inventory", "0018_inventory_tenant_integrity_guards")
    inventory_0019 = ("inventory", "0019_inventory_legacy_tenant_integrity_guards")

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        self.latest_targets = executor.loader.graph.leaf_nodes()
        executor.migrate([self.inventory_0017])
        self.apps = MigrationExecutor(connection).loader.project_state(
            [self.inventory_0017]
        ).apps

    def tearDown(self):
        try:
            MigrationExecutor(connection).migrate(self.latest_targets)
        finally:
            super().tearDown()

    def _create_tenants_and_inventory_refs(self):
        # accounts migrations remain at the latest schema while inventory is
        # rewound; use the current Business model so newly-added NOT NULL
        # columns (for example inventory_enabled) are populated by defaults.
        from accounts.models import Business

        Warehouse = self.apps.get_model("inventory", "Warehouse")
        Ingredient = self.apps.get_model("inventory", "Ingredient")

        business_a = Business.objects.create(name="Migration Tenant A", slug="migration-tenant-a")
        business_b = Business.objects.create(name="Migration Tenant B", slug="migration-tenant-b")
        warehouse_a = Warehouse.objects.create(business_id=business_a.pk, name="Migration Warehouse A")
        warehouse_b = Warehouse.objects.create(business_id=business_b.pk, name="Migration Warehouse B")
        ingredient_a = Ingredient.objects.create(
            business_id=business_a.pk, name="Migration Ingredient A", unit="kg"
        )
        ingredient_b = Ingredient.objects.create(
            business_id=business_b.pk, name="Migration Ingredient B", unit="kg"
        )
        return business_a, business_b, warehouse_a, warehouse_b, ingredient_a, ingredient_b

    def _assert_function_missing(self, signature):
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regprocedure(%s)", [signature])
            self.assertIsNone(cursor.fetchone()[0], signature)

    def _assert_triggers_missing(self, trigger_names):
        with connection.cursor() as cursor:
            for trigger_name in trigger_names:
                cursor.execute(
                    "SELECT EXISTS (SELECT 1 FROM pg_trigger WHERE NOT tgisinternal AND tgname = %s)",
                    [trigger_name],
                )
                self.assertFalse(cursor.fetchone()[0], trigger_name)

    def test_0018_real_preflight_rejects_corrupt_v1_rows_before_any_ddl(self):
        business_a, _business_b, _warehouse_a, warehouse_b, ingredient_a, _ingredient_b = (
            self._create_tenants_and_inventory_refs()
        )
        V1Stock = self.apps.get_model("inventory", "InventoryV1Stock")
        invalid_stock = V1Stock.objects.create(
            business_id=business_a.pk,
            warehouse=warehouse_b,
            ingredient=ingredient_a,
            unit="kg",
        )

        try:
            with self.assertRaisesRegex(
                DatabaseError, "Existing inventory_v1_stock rows violate tenant integrity"
            ):
                MigrationExecutor(connection).migrate([self.inventory_0018])

            self._assert_function_missing("inventory_v1_enforce_tenant_integrity()")
            self._assert_triggers_missing(
                [
                    "inventory_v1_stock_tenant_integrity",
                    "inventory_v1_stock_movement_tenant_integrity",
                    "inventory_operation_tenant_integrity",
                    "inventory_operation_line_tenant_integrity",
                    "inventory_reservation_tenant_integrity",
                    "inventory_reservation_line_tenant_integrity",
                ]
            )
        finally:
            V1Stock.objects.filter(pk=invalid_stock.pk).delete()

    def test_0019_real_preflight_rejects_legacy_corruption_before_any_ddl(self):
        self._create_tenants_and_inventory_refs()
        MigrationExecutor(connection).migrate([self.inventory_0018])
        self.apps = MigrationExecutor(connection).loader.project_state(
            [self.inventory_0018]
        ).apps

        from accounts.models import Business

        Warehouse = self.apps.get_model("inventory", "Warehouse")
        Ingredient = self.apps.get_model("inventory", "Ingredient")
        Stock = self.apps.get_model("inventory", "Stock")
        CompoundMaterialComponent = self.apps.get_model(
            "inventory", "CompoundMaterialComponent"
        )
        Recipe = self.apps.get_model("inventory", "Recipe")
        RecipeInput = self.apps.get_model("inventory", "RecipeInput")
        RecipeOutput = self.apps.get_model("inventory", "RecipeOutput")

        business_a = Business.objects.get(slug="migration-tenant-a")
        business_b = Business.objects.get(slug="migration-tenant-b")
        warehouse_a = Warehouse.objects.get(name="Migration Warehouse A")
        ingredient_a = Ingredient.objects.get(name="Migration Ingredient A")
        ingredient_b = Ingredient.objects.get(name="Migration Ingredient B")

        invalid_rows = [
            (
                Stock,
                {
                    "warehouse": warehouse_a,
                    "ingredient": ingredient_b,
                },
            ),
            (
                CompoundMaterialComponent,
                {
                    "compound": ingredient_a,
                    "ingredient": Ingredient.objects.create(
                        business_id=business_a.pk,
                        name="Migration Invalid Compound Component",
                        unit="kg",
                        preparation_level="raw",
                    ),
                    "quantity": Decimal("1"),
                    "unit": "kg",
                },
            ),
        ]
        recipe = Recipe.objects.create(business_id=business_a.pk, name="Migration Tenant Recipe")
        invalid_rows.extend(
            [
                (
                    RecipeInput,
                    {
                        "recipe": recipe,
                        "ingredient": ingredient_b,
                        "quantity": Decimal("1"),
                        "unit": "kg",
                    },
                ),
                (
                    RecipeOutput,
                    {
                        "recipe": recipe,
                        "ingredient": ingredient_b,
                        "quantity": Decimal("1"),
                        "unit": "kg",
                    },
                ),
            ]
        )

        for model, values in invalid_rows:
            with self.subTest(model=model.__name__):
                invalid_row = model.objects.create(**values)
                try:
                    with self.assertRaisesRegex(
                        DatabaseError,
                        "(Legacy Stock contains cross-business|Compound material components contain invalid tenant|Recipe input/output contains cross-business)",
                    ):
                        MigrationExecutor(connection).migrate([self.inventory_0019])

                    legacy_migration = import_module(
                        "inventory.migrations.0019_inventory_legacy_tenant_integrity_guards"
                    )
                    self._assert_function_missing("inventory_enforce_legacy_tenant_integrity()")
                    self._assert_triggers_missing(
                        [
                            *(
                                f"{table}_legacy_tenant_integrity"
                                for table in legacy_migration.CHILD_TABLES
                            ),
                            *(
                                f"{table}_parent_tenant_integrity"
                                for table in legacy_migration.PARENT_TABLES
                            ),
                        ]
                    )
                finally:
                    invalid_row.delete()
