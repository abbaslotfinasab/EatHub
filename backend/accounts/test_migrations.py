from importlib import import_module

from django.test import SimpleTestCase


class PurchasePermissionMigrationTests(SimpleTestCase):
    def test_purchase_permission_data_migration_is_explicitly_irreversible(self):
        migration_module = import_module(
            "accounts.migrations.0009_purchase_rbac_permissions"
        )
        operation = migration_module.Migration.operations[0]

        self.assertIsNone(operation.reverse_code)
