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
