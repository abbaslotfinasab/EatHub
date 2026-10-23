from importlib import import_module

from django.apps import apps
from django.db import connection
from django.test import SimpleTestCase, TransactionTestCase

from accounts.models import Business, Permission, Role, RolePermission


class PurchasePermissionMigrationTests(SimpleTestCase):
    def test_purchase_permission_data_migration_is_explicitly_irreversible(self):
        migration_module = import_module(
            "accounts.migrations.0009_purchase_rbac_permissions"
        )
        operation = migration_module.Migration.operations[0]

        self.assertIsNone(operation.reverse_code)


class PurchasePermissionMigrationForwardTests(TransactionTestCase):
    reset_sequences = True

    def test_forward_migration_grants_are_scoped_and_idempotent(self):
        migration_module = import_module(
            "accounts.migrations.0009_purchase_rbac_permissions"
        )
        businesses = [
            Business.objects.create(name="Purchase migration business one"),
            Business.objects.create(name="Purchase migration business two"),
        ]
        roles_by_business = {}
        for business in businesses:
            roles_by_business[business.id] = {}
            for code in ("OWNER", *migration_module.ROLE_GRANTS):
                roles_by_business[business.id][code] = Role.objects.create(
                    business=business,
                    name=code.title(),
                    code=code,
                    is_system=True,
                )

        custom_business = Business.objects.create(
            name="Purchase migration custom business"
        )
        custom_owner = Role.objects.create(
            business=custom_business,
            name="Custom owner",
            code="OWNER",
            is_system=False,
        )
        global_manager = Role.objects.create(
            business=None,
            name="Global manager",
            code="MANAGER",
            is_system=True,
        )
        unrelated_permission = Permission.objects.create(
            name="Unrelated permission",
            code="test.unrelated.permission",
        )
        custom_assignment = RolePermission.objects.create(
            role=custom_owner,
            permission=unrelated_permission,
        )

        operation = migration_module.Migration.operations[0]
        with connection.schema_editor() as schema_editor:
            operation.code(apps, schema_editor)

        permissions = Permission.objects.filter(
            code__in=migration_module.PURCHASE_PERMISSIONS
        )
        self.assertEqual(
            permissions.count(),
            len(migration_module.PURCHASE_PERMISSIONS),
        )
        self.assertEqual(
            dict(permissions.values_list("code", "name")),
            migration_module.PURCHASE_PERMISSIONS,
        )

        sensitive_permissions = {
            "purchase.requisition.approve",
            "purchase.order.dispatch",
            "purchase.order.cancel",
            "purchase.invoice.approve",
            "purchase.invoice.post",
            "purchase.invoice.cancel",
            "purchase.payment.create",
            "purchase.payment.allocate",
        }
        for business in businesses:
            for role_code, expected_codes in migration_module.ROLE_GRANTS.items():
                role = roles_by_business[business.id][role_code]
                actual_codes = set(
                    role.role_permissions.values_list("permission__code", flat=True)
                )
                self.assertEqual(actual_codes, expected_codes)
                self.assertTrue(sensitive_permissions.isdisjoint(actual_codes))

            owner = roles_by_business[business.id]["OWNER"]
            self.assertEqual(
                set(owner.role_permissions.values_list("permission__code", flat=True)),
                set(migration_module.PURCHASE_PERMISSIONS),
            )

        self.assertEqual(
            set(custom_owner.role_permissions.values_list("permission__code", flat=True)),
            {unrelated_permission.code},
        )
        self.assertFalse(global_manager.role_permissions.exists())
        self.assertTrue(RolePermission.objects.filter(pk=custom_assignment.pk).exists())

        permission_count = Permission.objects.count()
        assignment_count = RolePermission.objects.count()
        with connection.schema_editor() as schema_editor:
            operation.code(apps, schema_editor)

        self.assertEqual(Permission.objects.count(), permission_count)
        self.assertEqual(RolePermission.objects.count(), assignment_count)
