from django.db import migrations


VALIDATE_EXISTING_SQL = """
DO $
BEGIN
    IF EXISTS (
        SELECT 1 FROM inventory_v1_stock s
        JOIN inventory_warehouse w ON w.id = s.warehouse_id
        JOIN inventory_ingredient i ON i.id = s.ingredient_id
        WHERE s.business_id IS DISTINCT FROM w.business_id
           OR s.business_id IS DISTINCT FROM i.business_id
    ) THEN
        RAISE EXCEPTION 'Existing inventory_v1_stock rows violate tenant integrity';
    END IF;
    IF EXISTS (
        SELECT 1 FROM inventory_v1_stock_movement m
        JOIN inventory_v1_stock s ON s.id = m.stock_id
        WHERE m.business_id IS DISTINCT FROM s.business_id
    ) THEN
        RAISE EXCEPTION 'Existing inventory_v1_stock_movement rows violate tenant integrity';
    END IF;
    IF EXISTS (
        SELECT 1 FROM inventory_operation o
        JOIN inventory_warehouse w ON w.id = o.warehouse_id
        WHERE o.business_id IS DISTINCT FROM w.business_id
    ) OR EXISTS (
        SELECT 1 FROM inventory_operation o
        JOIN inventory_warehouse w ON w.id = o.destination_warehouse_id
        WHERE o.business_id IS DISTINCT FROM w.business_id
    ) THEN
        RAISE EXCEPTION 'Existing inventory_operation rows violate tenant integrity';
    END IF;
    IF EXISTS (
        SELECT 1 FROM inventory_operation_line l
        JOIN inventory_operation o ON o.id = l.operation_id
        JOIN inventory_ingredient i ON i.id = l.ingredient_id
        WHERE o.business_id IS DISTINCT FROM i.business_id
    ) THEN
        RAISE EXCEPTION 'Existing inventory_operation_line rows violate tenant integrity';
    END IF;
    IF EXISTS (
        SELECT 1 FROM inventory_reservation r
        JOIN inventory_warehouse w ON w.id = r.warehouse_id
        WHERE r.business_id IS DISTINCT FROM w.business_id
    ) THEN
        RAISE EXCEPTION 'Existing inventory_reservation rows violate tenant integrity';
    END IF;
    IF EXISTS (
        SELECT 1 FROM inventory_reservation_line l
        JOIN inventory_reservation r ON r.id = l.reservation_id
        JOIN inventory_ingredient i ON i.id = l.ingredient_id
        WHERE r.business_id IS DISTINCT FROM i.business_id
    ) THEN
        RAISE EXCEPTION 'Existing inventory_reservation_line rows violate tenant integrity';
    END IF;
END;
$
"""


CREATE_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION inventory_v1_enforce_tenant_integrity()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    related_business_id bigint;
    second_business_id bigint;
BEGIN
    IF TG_TABLE_NAME = 'inventory_v1_stock' THEN
        SELECT business_id INTO related_business_id
        FROM inventory_warehouse WHERE id = NEW.warehouse_id;
        SELECT business_id INTO second_business_id
        FROM inventory_ingredient WHERE id = NEW.ingredient_id;
        IF related_business_id IS DISTINCT FROM NEW.business_id
           OR second_business_id IS DISTINCT FROM NEW.business_id THEN
            RAISE EXCEPTION 'inventory stock references must belong to its business'
                USING ERRCODE = '23514';
        END IF;
    ELSIF TG_TABLE_NAME = 'inventory_v1_stock_movement' THEN
        SELECT business_id INTO related_business_id
        FROM inventory_v1_stock WHERE id = NEW.stock_id;
        IF related_business_id IS DISTINCT FROM NEW.business_id THEN
            RAISE EXCEPTION 'inventory movement and stock must belong to the same business'
                USING ERRCODE = '23514';
        END IF;
    ELSIF TG_TABLE_NAME = 'inventory_operation' THEN
        SELECT business_id INTO related_business_id
        FROM inventory_warehouse WHERE id = NEW.warehouse_id;
        IF related_business_id IS DISTINCT FROM NEW.business_id THEN
            RAISE EXCEPTION 'inventory operation warehouse must belong to its business'
                USING ERRCODE = '23514';
        END IF;
        IF NEW.destination_warehouse_id IS NOT NULL THEN
            SELECT business_id INTO related_business_id
            FROM inventory_warehouse WHERE id = NEW.destination_warehouse_id;
            IF related_business_id IS DISTINCT FROM NEW.business_id THEN
                RAISE EXCEPTION 'inventory operation destination must belong to its business'
                    USING ERRCODE = '23514';
            END IF;
        END IF;
    ELSIF TG_TABLE_NAME = 'inventory_operation_line' THEN
        SELECT business_id INTO related_business_id
        FROM inventory_operation WHERE id = NEW.operation_id;
        SELECT business_id INTO second_business_id
        FROM inventory_ingredient WHERE id = NEW.ingredient_id;
        IF related_business_id IS DISTINCT FROM second_business_id THEN
            RAISE EXCEPTION 'inventory operation line ingredient must belong to operation business'
                USING ERRCODE = '23514';
        END IF;
    ELSIF TG_TABLE_NAME = 'inventory_reservation' THEN
        SELECT business_id INTO related_business_id
        FROM inventory_warehouse WHERE id = NEW.warehouse_id;
        IF related_business_id IS DISTINCT FROM NEW.business_id THEN
            RAISE EXCEPTION 'inventory reservation warehouse must belong to its business'
                USING ERRCODE = '23514';
        END IF;
    ELSIF TG_TABLE_NAME = 'inventory_reservation_line' THEN
        SELECT business_id INTO related_business_id
        FROM inventory_reservation WHERE id = NEW.reservation_id;
        SELECT business_id INTO second_business_id
        FROM inventory_ingredient WHERE id = NEW.ingredient_id;
        IF related_business_id IS DISTINCT FROM second_business_id THEN
            RAISE EXCEPTION 'inventory reservation line ingredient must belong to reservation business'
                USING ERRCODE = '23514';
        END IF;
    END IF;
    RETURN NEW;
END;
$$
"""


def install_tenant_integrity_guards(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_editor.execute(VALIDATE_EXISTING_SQL)
    schema_editor.execute(CREATE_FUNCTION_SQL)
    for table in (
        "inventory_v1_stock",
        "inventory_v1_stock_movement",
        "inventory_operation",
        "inventory_operation_line",
        "inventory_reservation",
        "inventory_reservation_line",
    ):
        schema_editor.execute(
            f"""
            CREATE TRIGGER {table}_tenant_integrity
            BEFORE INSERT OR UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION inventory_v1_enforce_tenant_integrity()
            """
        )


def remove_tenant_integrity_guards(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    for table in (
        "inventory_v1_stock",
        "inventory_v1_stock_movement",
        "inventory_operation",
        "inventory_operation_line",
        "inventory_reservation",
        "inventory_reservation_line",
    ):
        schema_editor.execute(
            f"DROP TRIGGER IF EXISTS {table}_tenant_integrity ON {table}"
        )
    schema_editor.execute(
        "DROP FUNCTION IF EXISTS inventory_v1_enforce_tenant_integrity()"
    )


class Migration(migrations.Migration):
    dependencies = [("inventory", "0017_inventory_stock_movement_append_only")]

    operations = [
        migrations.RunPython(install_tenant_integrity_guards, remove_tenant_integrity_guards),
    ]
