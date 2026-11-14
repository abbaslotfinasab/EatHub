from importlib import import_module

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


class InventoryTenantMigrationReverseTests(SimpleTestCase):
    def test_0020_reverse_restores_unlocked_v1_destination_lookup(self):
        from unittest.mock import Mock

        migration = import_module(
            "inventory.migrations.0020_inventory_v1_tenant_locking"
        )
        schema_editor = Mock()
        schema_editor.connection.vendor = "postgresql"

        migration.restore_unlocked_tenant_guards(None, schema_editor)

        v1_function_sql = schema_editor.execute.call_args_list[0].args[0]
        self.assertIn(
            "FROM inventory_warehouse WHERE id = NEW.destination_warehouse_id",
            v1_function_sql,
        )
        self.assertNotIn(
            "FROM inventory_warehouse WHERE id = NEW.destination_warehouse_id FOR SHARE",
            v1_function_sql,
        )
