from django.db import migrations


PERMISSION = "inventory.order.fulfill"
PERMISSION_NAME = "Fulfill Order Inventory"


def add_order_inventory_permission(apps, schema_editor):
    database = schema_editor.connection.alias
    Permission = apps.get_model("accounts", "Permission")
    Role = apps.get_model("accounts", "Role")
    RolePermission = apps.get_model("accounts", "RolePermission")
    permission, _ = Permission.objects.using(database).get_or_create(
        code=PERMISSION,
        defaults={"name": PERMISSION_NAME},
    )
    roles = Role.objects.using(database).filter(
        code__in=("OWNER", "MANAGER", "CHEF"),
        is_system=True,
        business__isnull=False,
    )
    for role in roles.iterator():
        RolePermission.objects.using(database).get_or_create(
            role_id=role.pk,
            permission_id=permission.pk,
        )


class Migration(migrations.Migration):
    dependencies = [("accounts", "0012_inventory_compound_permission")]

    operations = [
        migrations.RunPython(add_order_inventory_permission, migrations.RunPython.noop),
    ]
