from django.db import migrations


def install_truncate_guard(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(
        """
        CREATE TRIGGER inventory_v1_stock_movement_no_truncate
        BEFORE TRUNCATE ON inventory_v1_stock_movement
        FOR EACH STATEMENT
        EXECUTE FUNCTION inventory_v1_reject_stock_movement_mutation()
        """
    )


def remove_truncate_guard(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(
        """
        DROP TRIGGER IF EXISTS inventory_v1_stock_movement_no_truncate
        ON inventory_v1_stock_movement
        """
    )


class Migration(migrations.Migration):
    dependencies = [("inventory", "0020_inventory_v1_tenant_locking")]

    operations = [
        migrations.RunPython(install_truncate_guard, remove_truncate_guard),
    ]
