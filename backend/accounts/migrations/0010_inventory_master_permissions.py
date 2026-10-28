from django.db import migrations


PERMISSIONS = {
    "inventory.item.manage": "Manage Inventory Items",
    "inventory.warehouse.manage": "Manage Warehouses",
}
MANAGER_GRANTS = set(PERMISSIONS)


def add_inventory_master_permissions(apps, schema_editor):
    database = schema_editor.connection.alias
    Permission = apps.get_model("accounts", "Permission")
    Role = apps.get_model("accounts", "Role")
    RolePermission = apps.get_model("accounts", "RolePermission")
    permissions = {}

    for code, name in PERMISSIONS.items():
        permission, _ = Permission.objects.using(database).get_or_create(
            code=code,
            defaults={"name": name},
        )
        permissions[code] = permission

    roles = Role.objects.using(database).filter(
        code__in=("OWNER", "MANAGER"),
        is_system=True,
        business__isnull=False,
    )
    for role in roles.iterator():
        grants = PERMISSIONS if role.code == "OWNER" else {
            code: PERMISSIONS[code] for code in MANAGER_GRANTS
        }
        for code in grants:
            RolePermission.objects.using(database).get_or_create(
                role_id=role.pk,
                permission_id=permissions[code].pk,
            )


class Migration(migrations.Migration):
    dependencies = [("accounts", "0009_purchase_rbac_permissions")]

    operations = [
        # Additive and deliberately non-destructive on reverse: ownership of
        # assignments cannot be distinguished from later administrative edits.
        migrations.RunPython(
            add_inventory_master_permissions,
            migrations.RunPython.noop,
        ),
    ]
