from importlib import import_module
from unittest.mock import Mock

from django.test import SimpleTestCase


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
            "FROM inventory_warehouse WHERE id = NEW.destination_warehouse_id FOR SHARE",
            legacy_function_sql,
        )
