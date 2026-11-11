from django.db import migrations


PERMISSION_CODE = "orders.view"
PERMISSION_NAME = "View Orders"
DEFAULT_ROLE_CODES = ("OWNER", "MANAGER", "CASHIER", "CHEF", "WAITER")


def grant_order_view_to_default_roles(apps, schema_editor):
    database = schema_editor.connection.alias
    Permission = apps.get_model("accounts", "Permission")
    Role = apps.get_model("accounts", "Role")
    RolePermission = apps.get_model("accounts", "RolePermission")

    permission, _ = Permission.objects.using(database).get_or_create(
        code=PERMISSION_CODE,
        defaults={"name": PERMISSION_NAME},
    )
    roles = Role.objects.using(database).filter(
        code__in=DEFAULT_ROLE_CODES,
        is_system=True,
        business__isnull=False,
    )
    for role in roles.iterator():
        RolePermission.objects.using(database).get_or_create(
            role_id=role.pk,
            permission_id=permission.pk,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0016_multi_active_memberships"),
    ]

    operations = [
        migrations.RunPython(
            grant_order_view_to_default_roles,
            migrations.RunPython.noop,
        ),
    ]
