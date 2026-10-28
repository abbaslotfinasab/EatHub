from django.db import migrations


PERMISSION = "inventory.recipe.manage"
PERMISSION_NAME = "Manage Recipes"


def add_recipe_permission(apps, schema_editor):
    database = schema_editor.connection.alias
    Permission = apps.get_model("accounts", "Permission")
    Role = apps.get_model("accounts", "Role")
    RolePermission = apps.get_model("accounts", "RolePermission")
    permission, _ = Permission.objects.using(database).get_or_create(
        code=PERMISSION,
        defaults={"name": PERMISSION_NAME},
    )
    roles = Role.objects.using(database).filter(
        code__in=("OWNER", "MANAGER"),
        is_system=True,
        business__isnull=False,
    )
    for role in roles.iterator():
        RolePermission.objects.using(database).get_or_create(
            role_id=role.pk,
            permission_id=permission.pk,
        )


class Migration(migrations.Migration):
    dependencies = [("accounts", "0010_inventory_master_permissions")]

    operations = [
        migrations.RunPython(add_recipe_permission, migrations.RunPython.noop),
    ]
