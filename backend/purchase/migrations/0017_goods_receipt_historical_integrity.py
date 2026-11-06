from django.db import migrations


def install_goods_receipt_history_guards(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    statements = [
        """
        CREATE OR REPLACE FUNCTION purchase_guard_goods_receipt_history()
        RETURNS trigger AS $$
        BEGIN
            IF TG_TABLE_NAME = 'purchase_goods_receipt_inventory_movement' THEN
                IF TG_OP IN ('UPDATE', 'DELETE') THEN
                    RAISE EXCEPTION 'Goods receipt movement links are immutable'
                        USING ERRCODE = '55000';
                END IF;
            ELSIF TG_TABLE_NAME = 'inventory_v1_stock_movement' THEN
                IF OLD.source_type = 'goods_receipt'
                   AND OLD.operation_kind = 'receive_stock'
                   AND TG_OP IN ('UPDATE', 'DELETE') THEN
                    RAISE EXCEPTION 'Goods receipt stock movements are immutable'
                        USING ERRCODE = '55000';
                END IF;
            ELSIF TG_TABLE_NAME = 'purchase_goodsreceiptitem' THEN
                IF TG_OP IN ('UPDATE', 'DELETE') THEN
                    RAISE EXCEPTION 'Goods receipt items are immutable historical records'
                        USING ERRCODE = '55000';
                END IF;
            ELSIF TG_TABLE_NAME = 'purchase_goodsreceipt' THEN
                IF TG_OP IN ('UPDATE', 'DELETE') THEN
                    RAISE EXCEPTION 'Goods receipts are immutable historical records'
                        USING ERRCODE = '55000';
                END IF;
            END IF;

            IF TG_OP = 'DELETE' THEN
                RETURN OLD;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """,
        """
        CREATE TRIGGER purchase_goods_receipt_link_immutable
        BEFORE UPDATE OR DELETE ON purchase_goods_receipt_inventory_movement
        FOR EACH ROW EXECUTE FUNCTION purchase_guard_goods_receipt_history();
        """,
        """
        CREATE TRIGGER purchase_goods_receipt_movement_immutable
        BEFORE UPDATE OR DELETE ON inventory_v1_stock_movement
        FOR EACH ROW EXECUTE FUNCTION purchase_guard_goods_receipt_history();
        """,
        """
        CREATE TRIGGER purchase_goods_receipt_item_immutable
        BEFORE UPDATE OR DELETE ON purchase_goodsreceiptitem
        FOR EACH ROW EXECUTE FUNCTION purchase_guard_goods_receipt_history();
        """,
        """
        CREATE TRIGGER purchase_goods_receipt_immutable
        BEFORE UPDATE OR DELETE ON purchase_goodsreceipt
        FOR EACH ROW EXECUTE FUNCTION purchase_guard_goods_receipt_history();
        """,
    ]
    with schema_editor.connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)


def remove_goods_receipt_history_guards(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    statements = [
        "DROP TRIGGER IF EXISTS purchase_goods_receipt_immutable ON purchase_goodsreceipt;",
        "DROP TRIGGER IF EXISTS purchase_goods_receipt_item_immutable ON purchase_goodsreceiptitem;",
        "DROP TRIGGER IF EXISTS purchase_goods_receipt_movement_immutable ON inventory_v1_stock_movement;",
        "DROP TRIGGER IF EXISTS purchase_goods_receipt_link_immutable ON purchase_goods_receipt_inventory_movement;",
        "DROP FUNCTION IF EXISTS purchase_guard_goods_receipt_history();",
    ]
    with schema_editor.connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)


class Migration(migrations.Migration):
    dependencies = [
        ("purchase", "0016_goods_receipt_inventory_movement_link"),
        ("inventory", "0005_retire_legacy_purchase_models_state"),
    ]

    operations = [
        migrations.RunPython(
            install_goods_receipt_history_guards,
            remove_goods_receipt_history_guards,
        ),
    ]
