from django.db import migrations


CREATE_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION inventory_v1_reject_stock_movement_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'inventory stock movements are append-only'
        USING ERRCODE = '55000';
END;
$$
"""

DROP_FUNCTION_SQL = """
DROP FUNCTION IF EXISTS inventory_v1_reject_stock_movement_mutation()
"""


def install_append_only_guard(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_editor.execute(CREATE_FUNCTION_SQL)
    schema_editor.execute(
        """
        CREATE TRIGGER inventory_v1_stock_movement_immutable
        BEFORE UPDATE OR DELETE ON inventory_v1_stock_movement
        FOR EACH ROW
        EXECUTE FUNCTION inventory_v1_reject_stock_movement_mutation()
        """
    )
    schema_editor.execute(
        """
        CREATE TRIGGER inventory_v1_stock_movement_no_truncate
        BEFORE TRUNCATE ON inventory_v1_stock_movement
        FOR EACH STATEMENT
        EXECUTE FUNCTION inventory_v1_reject_stock_movement_mutation()
        """
    )


def remove_append_only_guard(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_editor.execute(
        """
        DROP TRIGGER IF EXISTS inventory_v1_stock_movement_no_truncate
        ON inventory_v1_stock_movement
        """
    )
    schema_editor.execute(
        """
        DROP TRIGGER IF EXISTS inventory_v1_stock_movement_immutable
        ON inventory_v1_stock_movement
        """
    )
    schema_editor.execute(DROP_FUNCTION_SQL)


class Migration(migrations.Migration):
    dependencies = [("inventory", "0016_ingredient_allergen_enum_constraints")]

    operations = [
        migrations.RunPython(install_append_only_guard, remove_append_only_guard),
    ]
