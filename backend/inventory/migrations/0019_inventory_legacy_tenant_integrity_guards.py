from django.db import migrations


PREFLIGHT_SQL = """
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM inventory_stock s
        JOIN inventory_warehouse w ON w.id = s.warehouse_id
        JOIN inventory_ingredient i ON i.id = s.ingredient_id
        WHERE w.business_id IS DISTINCT FROM i.business_id
    ) THEN
        RAISE EXCEPTION 'Legacy Stock contains cross-business warehouse/ingredient references';
    END IF;

    IF EXISTS (
        SELECT 1 FROM inventory_compoundmaterialcomponent c
        JOIN inventory_ingredient parent ON parent.id = c.compound_id
        JOIN inventory_ingredient component ON component.id = c.ingredient_id
        WHERE parent.business_id IS DISTINCT FROM component.business_id
           OR parent.preparation_level IS DISTINCT FROM 'semi_prepared'
           OR component.preparation_level IS DISTINCT FROM 'raw'
           OR parent.id = component.id
    ) THEN
        RAISE EXCEPTION 'Compound material components contain invalid tenant or preparation-level references';
    END IF;

    IF EXISTS (
        SELECT 1 FROM inventory_recipeinput l
        JOIN inventory_recipe r ON r.id = l.recipe_id
        JOIN inventory_ingredient i ON i.id = l.ingredient_id
        WHERE r.business_id IS DISTINCT FROM i.business_id
    ) OR EXISTS (
        SELECT 1 FROM inventory_recipeoutput l
        JOIN inventory_recipe r ON r.id = l.recipe_id
        JOIN inventory_ingredient i ON i.id = l.ingredient_id
        WHERE r.business_id IS DISTINCT FROM i.business_id
    ) THEN
        RAISE EXCEPTION 'Recipe input/output contains cross-business ingredient references';
    END IF;
END;
$$
"""


GUARD_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION inventory_enforce_legacy_tenant_integrity()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    related_business_id bigint;
    second_business_id bigint;
    related_preparation_level text;
BEGIN
    IF TG_TABLE_NAME = 'inventory_stock' THEN
        SELECT business_id INTO related_business_id FROM inventory_warehouse WHERE id = NEW.warehouse_id;
        SELECT business_id INTO second_business_id FROM inventory_ingredient WHERE id = NEW.ingredient_id;
        IF related_business_id IS DISTINCT FROM second_business_id THEN
            RAISE EXCEPTION 'Legacy stock warehouse and ingredient must belong to the same business'
                USING ERRCODE = '23514';
        END IF;

    ELSIF TG_TABLE_NAME = 'inventory_compoundmaterialcomponent' THEN
        SELECT business_id, preparation_level INTO related_business_id, related_preparation_level
        FROM inventory_ingredient WHERE id = NEW.compound_id;
        IF related_business_id IS NULL OR related_preparation_level IS DISTINCT FROM 'semi_prepared' THEN
            RAISE EXCEPTION 'Compound component parent must be a semi-prepared ingredient'
                USING ERRCODE = '23514';
        END IF;
        SELECT business_id, preparation_level INTO second_business_id, related_preparation_level
        FROM inventory_ingredient WHERE id = NEW.ingredient_id;
        IF related_business_id IS DISTINCT FROM (
            SELECT business_id FROM inventory_ingredient WHERE id = NEW.compound_id
        ) OR related_preparation_level IS DISTINCT FROM 'raw' OR NEW.compound_id = NEW.ingredient_id THEN
            RAISE EXCEPTION 'Compound components must be raw ingredients owned by the compound business'
                USING ERRCODE = '23514';
        END IF;

    ELSIF TG_TABLE_NAME IN ('inventory_recipeinput', 'inventory_recipeoutput') THEN
        SELECT business_id INTO related_business_id FROM inventory_recipe WHERE id = NEW.recipe_id;
        SELECT business_id INTO second_business_id FROM inventory_ingredient WHERE id = NEW.ingredient_id;
        IF related_business_id IS DISTINCT FROM second_business_id THEN
            RAISE EXCEPTION 'Recipe and ingredient must belong to the same business'
                USING ERRCODE = '23514';
        END IF;

    ELSIF TG_TABLE_NAME = 'inventory_warehouse' AND TG_OP = 'UPDATE' THEN
        IF EXISTS (
            SELECT 1 FROM inventory_stock s
            JOIN inventory_ingredient i ON i.id = s.ingredient_id
            WHERE s.warehouse_id = NEW.id AND i.business_id IS DISTINCT FROM NEW.business_id
        ) OR EXISTS (
            SELECT 1 FROM inventory_v1_stock s
            JOIN inventory_ingredient i ON i.id = s.ingredient_id
            WHERE s.warehouse_id = NEW.id
              AND (s.business_id IS DISTINCT FROM NEW.business_id OR i.business_id IS DISTINCT FROM NEW.business_id)
        ) OR EXISTS (
            SELECT 1 FROM inventory_operation o
            WHERE (o.warehouse_id = NEW.id OR o.destination_warehouse_id = NEW.id)
              AND o.business_id IS DISTINCT FROM NEW.business_id
        ) OR EXISTS (
            SELECT 1 FROM inventory_reservation r
            WHERE r.warehouse_id = NEW.id AND r.business_id IS DISTINCT FROM NEW.business_id
        ) THEN
            RAISE EXCEPTION 'Warehouse business cannot change while referenced records would become cross-business'
                USING ERRCODE = '23514';
        END IF;

    ELSIF TG_TABLE_NAME = 'inventory_ingredient' AND TG_OP = 'UPDATE' THEN
        IF EXISTS (
            SELECT 1 FROM inventory_stock s
            JOIN inventory_warehouse w ON w.id = s.warehouse_id
            WHERE s.ingredient_id = NEW.id AND w.business_id IS DISTINCT FROM NEW.business_id
        ) OR EXISTS (
            SELECT 1 FROM inventory_v1_stock s
            JOIN inventory_warehouse w ON w.id = s.warehouse_id
            WHERE s.ingredient_id = NEW.id
              AND (s.business_id IS DISTINCT FROM NEW.business_id OR w.business_id IS DISTINCT FROM NEW.business_id)
        ) OR EXISTS (
            SELECT 1 FROM inventory_compoundmaterialcomponent c
            JOIN inventory_ingredient other ON other.id = c.ingredient_id
            WHERE c.compound_id = NEW.id AND other.business_id IS DISTINCT FROM NEW.business_id
        ) OR EXISTS (
            SELECT 1 FROM inventory_compoundmaterialcomponent c
            JOIN inventory_ingredient other ON other.id = c.compound_id
            WHERE c.ingredient_id = NEW.id AND other.business_id IS DISTINCT FROM NEW.business_id
        ) OR EXISTS (
            SELECT 1 FROM inventory_recipeinput l
            JOIN inventory_recipe r ON r.id = l.recipe_id
            WHERE l.ingredient_id = NEW.id AND r.business_id IS DISTINCT FROM NEW.business_id
        ) OR EXISTS (
            SELECT 1 FROM inventory_recipeoutput l
            JOIN inventory_recipe r ON r.id = l.recipe_id
            WHERE l.ingredient_id = NEW.id AND r.business_id IS DISTINCT FROM NEW.business_id
        ) OR EXISTS (
            SELECT 1 FROM inventory_operation_line l
            JOIN inventory_operation o ON o.id = l.operation_id
            WHERE l.ingredient_id = NEW.id AND o.business_id IS DISTINCT FROM NEW.business_id
        ) OR EXISTS (
            SELECT 1 FROM inventory_reservation_line l
            JOIN inventory_reservation r ON r.id = l.reservation_id
            WHERE l.ingredient_id = NEW.id AND r.business_id IS DISTINCT FROM NEW.business_id
        ) THEN
            RAISE EXCEPTION 'Ingredient business cannot change while referenced records would become cross-business'
                USING ERRCODE = '23514';
        END IF;

        IF NEW.preparation_level IS DISTINCT FROM OLD.preparation_level AND (
            (NEW.preparation_level <> 'semi_prepared' AND EXISTS (
                SELECT 1 FROM inventory_compoundmaterialcomponent c WHERE c.compound_id = NEW.id
            )) OR
            (NEW.preparation_level <> 'raw' AND EXISTS (
                SELECT 1 FROM inventory_compoundmaterialcomponent c WHERE c.ingredient_id = NEW.id
            ))
        ) THEN
            RAISE EXCEPTION 'Ingredient preparation level cannot invalidate compound component references'
                USING ERRCODE = '23514';
        END IF;

    ELSIF TG_TABLE_NAME = 'inventory_recipe' AND TG_OP = 'UPDATE' THEN
        IF EXISTS (
            SELECT 1 FROM inventory_recipeinput l
            JOIN inventory_ingredient i ON i.id = l.ingredient_id
            WHERE l.recipe_id = NEW.id AND i.business_id IS DISTINCT FROM NEW.business_id
        ) OR EXISTS (
            SELECT 1 FROM inventory_recipeoutput l
            JOIN inventory_ingredient i ON i.id = l.ingredient_id
            WHERE l.recipe_id = NEW.id AND i.business_id IS DISTINCT FROM NEW.business_id
        ) THEN
            RAISE EXCEPTION 'Recipe business cannot change while its ingredients belong to another business'
                USING ERRCODE = '23514';
        END IF;

    ELSIF TG_TABLE_NAME = 'inventory_v1_stock' AND TG_OP = 'UPDATE' THEN
        SELECT business_id INTO related_business_id FROM inventory_warehouse WHERE id = NEW.warehouse_id;
        SELECT business_id INTO second_business_id FROM inventory_ingredient WHERE id = NEW.ingredient_id;
        IF related_business_id IS DISTINCT FROM NEW.business_id
           OR second_business_id IS DISTINCT FROM NEW.business_id OR EXISTS (
            SELECT 1 FROM inventory_v1_stock_movement m
            WHERE m.stock_id = NEW.id AND m.business_id IS DISTINCT FROM NEW.business_id
        ) THEN
            RAISE EXCEPTION 'V1 stock business cannot change while movements exist for another business'
                USING ERRCODE = '23514';
        END IF;

    ELSIF TG_TABLE_NAME = 'inventory_operation' AND TG_OP = 'UPDATE' THEN
        SELECT business_id INTO related_business_id FROM inventory_warehouse WHERE id = NEW.warehouse_id;
        IF related_business_id IS DISTINCT FROM NEW.business_id THEN
            RAISE EXCEPTION 'Operation business must match its source warehouse'
                USING ERRCODE = '23514';
        END IF;
        IF NEW.destination_warehouse_id IS NOT NULL THEN
            SELECT business_id INTO related_business_id FROM inventory_warehouse WHERE id = NEW.destination_warehouse_id;
            IF related_business_id IS DISTINCT FROM NEW.business_id THEN
                RAISE EXCEPTION 'Operation business must match its destination warehouse'
                    USING ERRCODE = '23514';
            END IF;
        END IF;
        IF EXISTS (
            SELECT 1 FROM inventory_operation_line l
            JOIN inventory_ingredient i ON i.id = l.ingredient_id
            WHERE l.operation_id = NEW.id AND i.business_id IS DISTINCT FROM NEW.business_id
        ) THEN
            RAISE EXCEPTION 'Operation business cannot change while its lines belong to another business'
                USING ERRCODE = '23514';
        END IF;

    ELSIF TG_TABLE_NAME = 'inventory_reservation' AND TG_OP = 'UPDATE' THEN
        SELECT business_id INTO related_business_id FROM inventory_warehouse WHERE id = NEW.warehouse_id;
        IF related_business_id IS DISTINCT FROM NEW.business_id OR EXISTS (
            SELECT 1 FROM inventory_reservation_line l
            JOIN inventory_ingredient i ON i.id = l.ingredient_id
            WHERE l.reservation_id = NEW.id AND i.business_id IS DISTINCT FROM NEW.business_id
        ) THEN
            RAISE EXCEPTION 'Reservation business must match its warehouse and all line ingredients'
                USING ERRCODE = '23514';
        END IF;
    END IF;

    RETURN NEW;
END;
$$
"""


CHILD_TABLES = (
    "inventory_stock",
    "inventory_compoundmaterialcomponent",
    "inventory_recipeinput",
    "inventory_recipeoutput",
)

PARENT_TABLES = (
    "inventory_warehouse",
    "inventory_ingredient",
    "inventory_recipe",
    "inventory_v1_stock",
    "inventory_operation",
    "inventory_reservation",
)


def install_legacy_tenant_guards(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_editor.execute(PREFLIGHT_SQL)
    schema_editor.execute(GUARD_FUNCTION_SQL)

    for table in CHILD_TABLES:
        schema_editor.execute(
            f"""
            CREATE TRIGGER {table}_legacy_tenant_integrity
            BEFORE INSERT OR UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION inventory_enforce_legacy_tenant_integrity()
            """
        )

    for table in PARENT_TABLES:
        schema_editor.execute(
            f"""
            CREATE TRIGGER {table}_parent_tenant_integrity
            BEFORE UPDATE OF business_id, preparation_level ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION inventory_enforce_legacy_tenant_integrity()
            """
            if table == "inventory_ingredient"
            else f"""
            CREATE TRIGGER {table}_parent_tenant_integrity
            BEFORE UPDATE OF business_id ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION inventory_enforce_legacy_tenant_integrity()
            """
        )


def remove_legacy_tenant_guards(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    for table in CHILD_TABLES:
        schema_editor.execute(
            f"DROP TRIGGER IF EXISTS {table}_legacy_tenant_integrity ON {table}"
        )
    for table in PARENT_TABLES:
        schema_editor.execute(
            f"DROP TRIGGER IF EXISTS {table}_parent_tenant_integrity ON {table}"
        )
    schema_editor.execute(
        "DROP FUNCTION IF EXISTS inventory_enforce_legacy_tenant_integrity()"
    )


class Migration(migrations.Migration):
    dependencies = [("inventory", "0018_inventory_tenant_integrity_guards")]

    operations = [
        migrations.RunPython(install_legacy_tenant_guards, remove_legacy_tenant_guards),
    ]
