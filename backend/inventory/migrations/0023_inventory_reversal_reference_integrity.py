from django.db import migrations


CREATE_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION inventory_v1_validate_reversal_reference()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    source_stock_id bigint;
BEGIN
    IF NEW.movement_type <> 'reversal' THEN
        RETURN NEW;
    END IF;

    SELECT stock_id
    INTO source_stock_id
    FROM inventory_v1_stock_movement
    WHERE business_id = NEW.business_id
      AND source_type = NEW.reverses_source_type
      AND source_document_id = NEW.reverses_source_document_id
      AND source_line_id = NEW.reverses_source_line_id
      AND operation_kind = NEW.reverses_operation_kind
      AND movement_type <> 'reversal';

    IF NOT FOUND OR source_stock_id IS DISTINCT FROM NEW.stock_id THEN
        RAISE EXCEPTION 'inventory reversal must reference an existing non-reversal movement on the same stock'
            USING ERRCODE = '23514';
    END IF;

    RETURN NEW;
END;
$$
"""


DROP_FUNCTION_SQL = """
DROP FUNCTION IF EXISTS inventory_v1_validate_reversal_reference()
"""


def install_reversal_reference_guard(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_editor.execute(CREATE_FUNCTION_SQL)
    schema_editor.execute(
        """
        CREATE TRIGGER inventory_v1_stock_movement_reversal_reference
        BEFORE INSERT ON inventory_v1_stock_movement
        FOR EACH ROW
        EXECUTE FUNCTION inventory_v1_validate_reversal_reference()
        """
    )


def remove_reversal_reference_guard(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_editor.execute(
        """
        DROP TRIGGER IF EXISTS inventory_v1_stock_movement_reversal_reference
        ON inventory_v1_stock_movement
        """
    )
    schema_editor.execute(DROP_FUNCTION_SQL)


class Migration(migrations.Migration):
    dependencies = [("inventory", "0022_inventory_operation_idempotency")]

    operations = [
        migrations.RunPython(
            install_reversal_reference_guard,
            remove_reversal_reference_guard,
        ),
    ]
