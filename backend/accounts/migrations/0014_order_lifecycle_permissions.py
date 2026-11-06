from django.db import migrations


ORDER_DELETE_PERMISSION = "orders.delete"
ORDER_DELETE_PERMISSION_NAME = "Delete Unsettled Orders"
ORDER_CANCEL_PERMISSION = "orders.cancel"
ORDER_CANCEL_PERMISSION_NAME = "Cancel Orders"


def add_order_lifecycle_permissions(apps, schema_editor):
    database = schema_editor.connection.alias
    Permission = apps.get_model("accounts", "Permission")
    Role = apps.get_model("accounts", "Role")
    RolePermission = apps.get_model("accounts", "RolePermission")

    delete_permission, _ = Permission.objects.using(database).get_or_create(
        code=ORDER_DELETE_PERMISSION,
        defaults={"name": ORDER_DELETE_PERMISSION_NAME},
    )
    cancel_permission, _ = Permission.objects.using(database).get_or_create(
        code=ORDER_CANCEL_PERMISSION,
        defaults={"name": ORDER_CANCEL_PERMISSION_NAME},
    )

    owner_roles = Role.objects.using(database).filter(
        code="OWNER",
        is_system=True,
        business__isnull=False,
    )
    for role in owner_roles.iterator():
        RolePermission.objects.using(database).get_or_create(
            role_id=role.pk,
            permission_id=delete_permission.pk,
        )

    manager_roles = Role.objects.using(database).filter(
        code="MANAGER",
        is_system=True,
        business__isnull=False,
    )
    for role in manager_roles.iterator():
        RolePermission.objects.using(database).get_or_create(
            role_id=role.pk,
            permission_id=cancel_permission.pk,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0013_order_inventory_permission"),
    ]

    operations = [
        migrations.RunPython(
            add_order_lifecycle_permissions,
            migrations.RunPython.noop,
        ),
    ]
