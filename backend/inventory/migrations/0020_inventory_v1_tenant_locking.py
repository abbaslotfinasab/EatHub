from django.db import migrations


V1_LOCKED_FUNCTION_SQL = """
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
        FROM inventory_warehouse WHERE id = NEW.warehouse_id FOR SHARE;
        SELECT business_id INTO second_business_id
        FROM inventory_ingredient WHERE id = NEW.ingredient_id FOR SHARE;
        IF related_business_id IS DISTINCT FROM NEW.business_id
           OR second_business_id IS DISTINCT FROM NEW.business_id THEN
            RAISE EXCEPTION 'inventory stock references must belong to its business'
                USING ERRCODE = '23514';
        END IF;
    ELSIF TG_TABLE_NAME = 'inventory_v1_stock_movement' THEN
        SELECT business_id INTO related_business_id
        FROM inventory_v1_stock WHERE id = NEW.stock_id FOR SHARE;
        IF related_business_id IS DISTINCT FROM NEW.business_id THEN
            RAISE EXCEPTION 'inventory movement and stock must belong to the same business'
                USING ERRCODE = '23514';
        END IF;
    ELSIF TG_TABLE_NAME = 'inventory_operation' THEN
        SELECT business_id INTO related_business_id
        FROM inventory_warehouse WHERE id = NEW.warehouse_id FOR SHARE;
        IF related_business_id IS DISTINCT FROM NEW.business_id THEN
            RAISE EXCEPTION 'inventory operation warehouse must belong to its business'
                USING ERRCODE = '23514';
        END IF;
        IF NEW.destination_warehouse_id IS NOT NULL THEN
            SELECT business_id INTO related_business_id
            FROM inventory_warehouse WHERE id = NEW.destination_warehouse_id FOR SHARE;
            IF related_business_id IS DISTINCT FROM NEW.business_id THEN
                RAISE EXCEPTION 'inventory operation destination must belong to its business'
                    USING ERRCODE = '23514';
            END IF;
        END IF;
    ELSIF TG_TABLE_NAME = 'inventory_operation_line' THEN
        SELECT business_id INTO related_business_id
        FROM inventory_operation WHERE id = NEW.operation_id FOR SHARE;
        SELECT business_id INTO second_business_id
        FROM inventory_ingredient WHERE id = NEW.ingredient_id FOR SHARE;
        IF related_business_id IS DISTINCT FROM second_business_id THEN
            RAISE EXCEPTION 'inventory operation line ingredient must belong to operation business'
                USING ERRCODE = '23514';
        END IF;
    ELSIF TG_TABLE_NAME = 'inventory_reservation' THEN
        SELECT business_id INTO related_business_id
        FROM inventory_warehouse WHERE id = NEW.warehouse_id FOR SHARE;
        IF related_business_id IS DISTINCT FROM NEW.business_id THEN
            RAISE EXCEPTION 'inventory reservation warehouse must belong to its business'
                USING ERRCODE = '23514';
        END IF;
    ELSIF TG_TABLE_NAME = 'inventory_reservation_line' THEN
        SELECT business_id INTO related_business_id
        FROM inventory_reservation WHERE id = NEW.reservation_id FOR SHARE;
        SELECT business_id INTO second_business_id
        FROM inventory_ingredient WHERE id = NEW.ingredient_id FOR SHARE;
        IF related_business_id IS DISTINCT FROM second_business_id THEN
            RAISE EXCEPTION 'inventory reservation line ingredient must belong to reservation business'
                USING ERRCODE = '23514';
        END IF;
    END IF;
    RETURN NEW;
END;
$$
"""


LEGACY_LOCKED_FUNCTION_SQL = """
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
        SELECT business_id INTO related_business_id FROM inventory_warehouse WHERE id = NEW.warehouse_id FOR SHARE;
        SELECT business_id INTO second_business_id FROM inventory_ingredient WHERE id = NEW.ingredient_id FOR SHARE;
        IF related_business_id IS DISTINCT FROM second_business_id THEN
            RAISE EXCEPTION 'Legacy stock warehouse and ingredient must belong to the same business'
                USING ERRCODE = '23514';
        END IF;

    ELSIF TG_TABLE_NAME = 'inventory_compoundmaterialcomponent' THEN
        SELECT business_id, preparation_level INTO related_business_id, related_preparation_level
        FROM inventory_ingredient WHERE id = NEW.compound_id FOR SHARE;
        IF related_business_id IS NULL OR related_preparation_level IS DISTINCT FROM 'semi_prepared' THEN
            RAISE EXCEPTION 'Compound component parent must be a semi-prepared ingredient'
                USING ERRCODE = '23514';
        END IF;
        SELECT business_id, preparation_level INTO second_business_id, related_preparation_level
        FROM inventory_ingredient WHERE id = NEW.ingredient_id FOR SHARE;
        IF second_business_id IS DISTINCT FROM related_business_id
           OR related_preparation_level IS DISTINCT FROM 'raw'
           OR NEW.compound_id = NEW.ingredient_id THEN
            RAISE EXCEPTION 'Compound components must be raw ingredients owned by the compound business'
                USING ERRCODE = '23514';
        END IF;

    ELSIF TG_TABLE_NAME IN ('inventory_recipeinput', 'inventory_recipeoutput') THEN
        SELECT business_id INTO related_business_id FROM inventory_recipe WHERE id = NEW.recipe_id FOR SHARE;
        SELECT business_id INTO second_business_id FROM inventory_ingredient WHERE id = NEW.ingredient_id FOR SHARE;
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
        SELECT business_id INTO related_business_id FROM inventory_warehouse WHERE id = NEW.warehouse_id FOR SHARE;
        SELECT business_id INTO second_business_id FROM inventory_ingredient WHERE id = NEW.ingredient_id FOR SHARE;
        IF related_business_id IS DISTINCT FROM NEW.business_id
           OR second_business_id IS DISTINCT FROM NEW.business_id OR EXISTS (
            SELECT 1 FROM inventory_v1_stock_movement m
            WHERE m.stock_id = NEW.id AND m.business_id IS DISTINCT FROM NEW.business_id
        ) THEN
            RAISE EXCEPTION 'V1 stock business cannot change while movements exist for another business'
                USING ERRCODE = '23514';
        END IF;

    ELSIF TG_TABLE_NAME = 'inventory_operation' AND TG_OP = 'UPDATE' THEN
        SELECT business_id INTO related_business_id FROM inventory_warehouse WHERE id = NEW.warehouse_id FOR SHARE;
        IF related_business_id IS DISTINCT FROM NEW.business_id THEN
            RAISE EXCEPTION 'Operation business must match its source warehouse'
                USING ERRCODE = '23514';
        END IF;
        IF NEW.destination_warehouse_id IS NOT NULL THEN
            SELECT business_id INTO related_business_id FROM inventory_warehouse WHERE id = NEW.destination_warehouse_id FOR SHARE;
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
        SELECT business_id INTO related_business_id FROM inventory_warehouse WHERE id = NEW.warehouse_id FOR SHARE;
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


def install_locked_tenant_guards(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(V1_LOCKED_FUNCTION_SQL)
    schema_editor.execute(LEGACY_LOCKED_FUNCTION_SQL)


def restore_unlocked_tenant_guards(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    # Restore the pre-0020 function bodies for a faithful reverse migration.
    schema_editor.execute(
        """
        CREATE OR REPLACE FUNCTION inventory_v1_enforce_tenant_integrity()
        RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE related_business_id bigint; second_business_id bigint;
        BEGIN
            IF TG_TABLE_NAME = 'inventory_v1_stock' THEN
                SELECT business_id INTO related_business_id FROM inventory_warehouse WHERE id = NEW.warehouse_id;
                SELECT business_id INTO second_business_id FROM inventory_ingredient WHERE id = NEW.ingredient_id;
                IF related_business_id IS DISTINCT FROM NEW.business_id OR second_business_id IS DISTINCT FROM NEW.business_id THEN
                    RAISE EXCEPTION 'inventory stock references must belong to its business' USING ERRCODE = '23514';
                END IF;
            ELSIF TG_TABLE_NAME = 'inventory_v1_stock_movement' THEN
                SELECT business_id INTO related_business_id FROM inventory_v1_stock WHERE id = NEW.stock_id;
                IF related_business_id IS DISTINCT FROM NEW.business_id THEN
                    RAISE EXCEPTION 'inventory movement and stock must belong to the same business' USING ERRCODE = '23514';
                END IF;
            ELSIF TG_TABLE_NAME = 'inventory_operation' THEN
                SELECT business_id INTO related_business_id FROM inventory_warehouse WHERE id = NEW.warehouse_id;
                IF related_business_id IS DISTINCT FROM NEW.business_id THEN
                    RAISE EXCEPTION 'inventory operation warehouse must belong to its business' USING ERRCODE = '23514';
                END IF;
                IF NEW.destination_warehouse_id IS NOT NULL THEN
                    SELECT business_id INTO related_business_id FROM inventory_warehouse WHERE id = NEW.destination_warehouse_id;
                    IF related_business_id IS DISTINCT FROM NEW.business_id THEN
                        RAISE EXCEPTION 'inventory operation destination must belong to its business' USING ERRCODE = '23514';
                    END IF;
                END IF;
            ELSIF TG_TABLE_NAME = 'inventory_operation_line' THEN
                SELECT business_id INTO related_business_id FROM inventory_operation WHERE id = NEW.operation_id;
                SELECT business_id INTO second_business_id FROM inventory_ingredient WHERE id = NEW.ingredient_id;
                IF related_business_id IS DISTINCT FROM second_business_id THEN
                    RAISE EXCEPTION 'inventory operation line ingredient must belong to operation business' USING ERRCODE = '23514';
                END IF;
            ELSIF TG_TABLE_NAME = 'inventory_reservation' THEN
                SELECT business_id INTO related_business_id FROM inventory_warehouse WHERE id = NEW.warehouse_id;
                IF related_business_id IS DISTINCT FROM NEW.business_id THEN
                    RAISE EXCEPTION 'inventory reservation warehouse must belong to its business' USING ERRCODE = '23514';
                END IF;
            ELSIF TG_TABLE_NAME = 'inventory_reservation_line' THEN
                SELECT business_id INTO related_business_id FROM inventory_reservation WHERE id = NEW.reservation_id;
                SELECT business_id INTO second_business_id FROM inventory_ingredient WHERE id = NEW.ingredient_id;
                IF related_business_id IS DISTINCT FROM second_business_id THEN
                    RAISE EXCEPTION 'inventory reservation line ingredient must belong to reservation business' USING ERRCODE = '23514';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$
        """
    )
    schema_editor.execute(
        """
        CREATE OR REPLACE FUNCTION inventory_enforce_legacy_tenant_integrity()
        RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE related_business_id bigint; second_business_id bigint; related_preparation_level text;
        BEGIN
            IF TG_TABLE_NAME = 'inventory_stock' THEN
                SELECT business_id INTO related_business_id FROM inventory_warehouse WHERE id = NEW.warehouse_id FOR SHARE;
                SELECT business_id INTO second_business_id FROM inventory_ingredient WHERE id = NEW.ingredient_id FOR SHARE;
                IF related_business_id IS DISTINCT FROM second_business_id THEN
                    RAISE EXCEPTION 'Legacy stock warehouse and ingredient must belong to the same business' USING ERRCODE = '23514';
                END IF;
            ELSIF TG_TABLE_NAME = 'inventory_compoundmaterialcomponent' THEN
                SELECT business_id, preparation_level INTO related_business_id, related_preparation_level FROM inventory_ingredient WHERE id = NEW.compound_id FOR SHARE;
                IF related_business_id IS NULL OR related_preparation_level IS DISTINCT FROM 'semi_prepared' THEN
                    RAISE EXCEPTION 'Compound component parent must be a semi-prepared ingredient' USING ERRCODE = '23514';
                END IF;
                SELECT business_id, preparation_level INTO second_business_id, related_preparation_level FROM inventory_ingredient WHERE id = NEW.ingredient_id FOR SHARE;
                IF second_business_id IS DISTINCT FROM related_business_id OR related_preparation_level IS DISTINCT FROM 'raw' OR NEW.compound_id = NEW.ingredient_id THEN
                    RAISE EXCEPTION 'Compound components must be raw ingredients owned by the compound business' USING ERRCODE = '23514';
                END IF;
            ELSIF TG_TABLE_NAME IN ('inventory_recipeinput', 'inventory_recipeoutput') THEN
                SELECT business_id INTO related_business_id FROM inventory_recipe WHERE id = NEW.recipe_id FOR SHARE;
                SELECT business_id INTO second_business_id FROM inventory_ingredient WHERE id = NEW.ingredient_id FOR SHARE;
                IF related_business_id IS DISTINCT FROM second_business_id THEN
                    RAISE EXCEPTION 'Recipe and ingredient must belong to the same business' USING ERRCODE = '23514';
                END IF;
            ELSIF TG_TABLE_NAME = 'inventory_warehouse' AND TG_OP = 'UPDATE' THEN
                IF EXISTS (SELECT 1 FROM inventory_stock s JOIN inventory_ingredient i ON i.id = s.ingredient_id WHERE s.warehouse_id = NEW.id AND i.business_id IS DISTINCT FROM NEW.business_id)
                   OR EXISTS (SELECT 1 FROM inventory_v1_stock s JOIN inventory_ingredient i ON i.id = s.ingredient_id WHERE s.warehouse_id = NEW.id AND (s.business_id IS DISTINCT FROM NEW.business_id OR i.business_id IS DISTINCT FROM NEW.business_id))
                   OR EXISTS (SELECT 1 FROM inventory_operation o WHERE (o.warehouse_id = NEW.id OR o.destination_warehouse_id = NEW.id) AND o.business_id IS DISTINCT FROM NEW.business_id)
                   OR EXISTS (SELECT 1 FROM inventory_reservation r WHERE r.warehouse_id = NEW.id AND r.business_id IS DISTINCT FROM NEW.business_id) THEN
                    RAISE EXCEPTION 'Warehouse business cannot change while referenced records would become cross-business' USING ERRCODE = '23514';
                END IF;
            ELSIF TG_TABLE_NAME = 'inventory_ingredient' AND TG_OP = 'UPDATE' THEN
                IF EXISTS (SELECT 1 FROM inventory_stock s JOIN inventory_warehouse w ON w.id = s.warehouse_id WHERE s.ingredient_id = NEW.id AND w.business_id IS DISTINCT FROM NEW.business_id)
                   OR EXISTS (SELECT 1 FROM inventory_v1_stock s JOIN inventory_warehouse w ON w.id = s.warehouse_id WHERE s.ingredient_id = NEW.id AND (s.business_id IS DISTINCT FROM NEW.business_id OR w.business_id IS DISTINCT FROM NEW.business_id))
                   OR EXISTS (SELECT 1 FROM inventory_compoundmaterialcomponent c JOIN inventory_ingredient other ON other.id = c.ingredient_id WHERE c.compound_id = NEW.id AND other.business_id IS DISTINCT FROM NEW.business_id)
                   OR EXISTS (SELECT 1 FROM inventory_compoundmaterialcomponent c JOIN inventory_ingredient other ON other.id = c.compound_id WHERE c.ingredient_id = NEW.id AND other.business_id IS DISTINCT FROM NEW.business_id)
                   OR EXISTS (SELECT 1 FROM inventory_recipeinput l JOIN inventory_recipe r ON r.id = l.recipe_id WHERE l.ingredient_id = NEW.id AND r.business_id IS DISTINCT FROM NEW.business_id)
                   OR EXISTS (SELECT 1 FROM inventory_recipeoutput l JOIN inventory_recipe r ON r.id = l.recipe_id WHERE l.ingredient_id = NEW.id AND r.business_id IS DISTINCT FROM NEW.business_id)
                   OR EXISTS (SELECT 1 FROM inventory_operation_line l JOIN inventory_operation o ON o.id = l.operation_id WHERE l.ingredient_id = NEW.id AND o.business_id IS DISTINCT FROM NEW.business_id)
                   OR EXISTS (SELECT 1 FROM inventory_reservation_line l JOIN inventory_reservation r ON r.id = l.reservation_id WHERE l.ingredient_id = NEW.id AND r.business_id IS DISTINCT FROM NEW.business_id) THEN
                    RAISE EXCEPTION 'Ingredient business cannot change while referenced records would become cross-business' USING ERRCODE = '23514';
                END IF;
                IF NEW.preparation_level IS DISTINCT FROM OLD.preparation_level AND (
                    (NEW.preparation_level <> 'semi_prepared' AND EXISTS (SELECT 1 FROM inventory_compoundmaterialcomponent c WHERE c.compound_id = NEW.id))
                    OR (NEW.preparation_level <> 'raw' AND EXISTS (SELECT 1 FROM inventory_compoundmaterialcomponent c WHERE c.ingredient_id = NEW.id))
                ) THEN
                    RAISE EXCEPTION 'Ingredient preparation level cannot invalidate compound component references' USING ERRCODE = '23514';
                END IF;
            ELSIF TG_TABLE_NAME = 'inventory_recipe' AND TG_OP = 'UPDATE' THEN
                IF EXISTS (SELECT 1 FROM inventory_recipeinput l JOIN inventory_ingredient i ON i.id = l.ingredient_id WHERE l.recipe_id = NEW.id AND i.business_id IS DISTINCT FROM NEW.business_id)
                   OR EXISTS (SELECT 1 FROM inventory_recipeoutput l JOIN inventory_ingredient i ON i.id = l.ingredient_id WHERE l.recipe_id = NEW.id AND i.business_id IS DISTINCT FROM NEW.business_id) THEN
                    RAISE EXCEPTION 'Recipe business cannot change while its ingredients belong to another business' USING ERRCODE = '23514';
                END IF;
            ELSIF TG_TABLE_NAME = 'inventory_v1_stock' AND TG_OP = 'UPDATE' THEN
                SELECT business_id INTO related_business_id FROM inventory_warehouse WHERE id = NEW.warehouse_id FOR SHARE;
                SELECT business_id INTO second_business_id FROM inventory_ingredient WHERE id = NEW.ingredient_id FOR SHARE;
                IF related_business_id IS DISTINCT FROM NEW.business_id OR second_business_id IS DISTINCT FROM NEW.business_id OR EXISTS (SELECT 1 FROM inventory_v1_stock_movement m WHERE m.stock_id = NEW.id AND m.business_id IS DISTINCT FROM NEW.business_id) THEN
                    RAISE EXCEPTION 'V1 stock business cannot change while movements exist for another business' USING ERRCODE = '23514';
                END IF;
            ELSIF TG_TABLE_NAME = 'inventory_operation' AND TG_OP = 'UPDATE' THEN
                SELECT business_id INTO related_business_id FROM inventory_warehouse WHERE id = NEW.warehouse_id FOR SHARE;
                IF related_business_id IS DISTINCT FROM NEW.business_id THEN
                    RAISE EXCEPTION 'Operation business must match its source warehouse' USING ERRCODE = '23514';
                END IF;
                IF NEW.destination_warehouse_id IS NOT NULL THEN
                    SELECT business_id INTO related_business_id FROM inventory_warehouse WHERE id = NEW.destination_warehouse_id;
                    IF related_business_id IS DISTINCT FROM NEW.business_id THEN
                        RAISE EXCEPTION 'Operation business must match its destination warehouse' USING ERRCODE = '23514';
                    END IF;
                END IF;
                IF EXISTS (SELECT 1 FROM inventory_operation_line l JOIN inventory_ingredient i ON i.id = l.ingredient_id WHERE l.operation_id = NEW.id AND i.business_id IS DISTINCT FROM NEW.business_id) THEN
                    RAISE EXCEPTION 'Operation business cannot change while its lines belong to another business' USING ERRCODE = '23514';
                END IF;
            ELSIF TG_TABLE_NAME = 'inventory_reservation' AND TG_OP = 'UPDATE' THEN
                SELECT business_id INTO related_business_id FROM inventory_warehouse WHERE id = NEW.warehouse_id FOR SHARE;
                IF related_business_id IS DISTINCT FROM NEW.business_id OR EXISTS (SELECT 1 FROM inventory_reservation_line l JOIN inventory_ingredient i ON i.id = l.ingredient_id WHERE l.reservation_id = NEW.id AND i.business_id IS DISTINCT FROM NEW.business_id) THEN
                    RAISE EXCEPTION 'Reservation business must match its warehouse and all line ingredients' USING ERRCODE = '23514';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$
        """
    )


class Migration(migrations.Migration):
    dependencies = [("inventory", "0019_inventory_legacy_tenant_integrity_guards")]

    operations = [
        migrations.RunPython(install_locked_tenant_guards, restore_unlocked_tenant_guards),
    ]
