from django.db import migrations


CREATE_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION purchase_validate_goods_receipt_inventory_link()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    receipt_business_id bigint;
    receipt_id bigint;
    receipt_warehouse_id bigint;
    receipt_purchase_order_id bigint;
    item_id bigint;
    item_purchase_order_id bigint;
    item_ingredient_id bigint;
    order_business_id bigint;
    supplier_business_id bigint;
    movement_business_id bigint;
    movement_source_type text;
    movement_source_document_id bigint;
    movement_source_line_id bigint;
    movement_operation_kind text;
    movement_type text;
    movement_direction text;
    stock_business_id bigint;
    stock_ingredient_id bigint;
    movement_warehouse_id bigint;
    warehouse_business_id bigint;
    ingredient_business_id bigint;
BEGIN
    SELECT receipt.business_id, receipt.id, receipt.purchase_order_id,
           receipt.warehouse_id,
           receipt_item.id, purchase_order_item.purchase_order_id,
           purchase_order_item.ingredient_id, purchase_order.business_id,
           supplier.business_id
    INTO receipt_business_id, receipt_id, receipt_purchase_order_id,
         receipt_warehouse_id,
         item_id, item_purchase_order_id, item_ingredient_id,
         order_business_id, supplier_business_id
    FROM purchase_goodsreceiptitem AS receipt_item
    JOIN purchase_goodsreceipt AS receipt ON receipt.id = receipt_item.receipt_id
    JOIN purchase_purchaseorderitem AS purchase_order_item
      ON purchase_order_item.id = receipt_item.purchase_order_item_id
    JOIN purchase_purchaseorder AS purchase_order
      ON purchase_order.id = purchase_order_item.purchase_order_id
    JOIN purchase_supplier AS supplier ON supplier.id = purchase_order.supplier_id
    WHERE receipt_item.id = NEW.receipt_item_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Goods receipt inventory link requires a valid receipt item'
            USING ERRCODE = '23514';
    END IF;

    SELECT movement.business_id, movement.source_type,
           movement.source_document_id, movement.source_line_id,
           movement.operation_kind, movement.movement_type, movement.direction,
           stock.business_id, stock.ingredient_id, stock.warehouse_id,
           warehouse.business_id, ingredient.business_id
    INTO movement_business_id, movement_source_type,
         movement_source_document_id, movement_source_line_id,
         movement_operation_kind, movement_type, movement_direction,
         stock_business_id, stock_ingredient_id, movement_warehouse_id,
         warehouse_business_id, ingredient_business_id
    FROM inventory_v1_stock_movement AS movement
    JOIN inventory_v1_stock AS stock ON stock.id = movement.stock_id
    JOIN inventory_warehouse AS warehouse ON warehouse.id = stock.warehouse_id
    JOIN inventory_ingredient AS ingredient ON ingredient.id = stock.ingredient_id
    WHERE movement.id = NEW.movement_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Goods receipt inventory link requires a valid stock movement'
            USING ERRCODE = '23514';
    END IF;

    IF receipt_purchase_order_id IS DISTINCT FROM item_purchase_order_id
       OR order_business_id IS DISTINCT FROM receipt_business_id
       OR supplier_business_id IS DISTINCT FROM receipt_business_id
       OR movement_business_id IS DISTINCT FROM receipt_business_id
       OR movement_source_type IS DISTINCT FROM 'goods_receipt'
       OR movement_source_document_id IS DISTINCT FROM receipt_id
       OR movement_source_line_id IS DISTINCT FROM item_id
       OR movement_operation_kind IS DISTINCT FROM 'receive_stock'
       OR movement_type IS DISTINCT FROM 'receipt'
       OR movement_direction IS DISTINCT FROM 'in'
       OR stock_business_id IS DISTINCT FROM receipt_business_id
       OR warehouse_business_id IS DISTINCT FROM receipt_business_id
       OR ingredient_business_id IS DISTINCT FROM receipt_business_id
       OR stock_ingredient_id IS DISTINCT FROM item_ingredient_id
       OR (receipt_warehouse_id IS NOT NULL
           AND movement_warehouse_id IS DISTINCT FROM receipt_warehouse_id)
    THEN
        RAISE EXCEPTION 'Goods receipt inventory link does not match its receipt, tenant, item, or movement identity'
            USING ERRCODE = '23514';
    END IF;

    RETURN NEW;
END;
$$
"""


DROP_FUNCTION_SQL = """
DROP FUNCTION IF EXISTS purchase_validate_goods_receipt_inventory_link()
"""


def install_goods_receipt_inventory_link_guard(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(CREATE_FUNCTION_SQL)
    schema_editor.execute(
        """
        CREATE TRIGGER purchase_goods_receipt_inventory_link_validate
        BEFORE INSERT ON purchase_goods_receipt_inventory_movement
        FOR EACH ROW
        EXECUTE FUNCTION purchase_validate_goods_receipt_inventory_link()
        """
    )


def remove_goods_receipt_inventory_link_guard(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(
        """
        DROP TRIGGER IF EXISTS purchase_goods_receipt_inventory_link_validate
        ON purchase_goods_receipt_inventory_movement
        """
    )
    schema_editor.execute(DROP_FUNCTION_SQL)


class Migration(migrations.Migration):
    dependencies = [
        ("purchase", "0021_goods_receipt_inventory_link_integrity"),
        ("inventory", "0023_inventory_reversal_reference_integrity"),
    ]

    operations = [
        migrations.RunPython(
            install_goods_receipt_inventory_link_guard,
            remove_goods_receipt_inventory_link_guard,
        ),
    ]
