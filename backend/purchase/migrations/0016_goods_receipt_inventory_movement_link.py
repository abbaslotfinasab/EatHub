from django.db import migrations, models
import django.db.models.deletion


def backfill_receipt_movement_links(apps, schema_editor):
    GoodsReceiptItem = apps.get_model("purchase", "GoodsReceiptItem")
    StockMovement = apps.get_model("inventory", "InventoryV1StockMovement")
    database = schema_editor.connection.alias

    movements = (
        StockMovement.objects.using(database)
        .filter(source_type="goods_receipt", operation_kind="receive_stock")
        .select_related("stock")
        .order_by("pk")
    )
    for movement in movements.iterator():
        line = (
            GoodsReceiptItem.objects.using(database)
            .filter(
                pk=movement.source_line_id,
                receipt_id=movement.source_document_id,
                receipt__business_id=movement.business_id,
                purchase_order_item__ingredient_id=movement.stock.ingredient_id,
            )
            .first()
        )
        if line is not None and line.inventory_movement_id is None:
            line.inventory_movement_id = movement.pk
            line.save(using=database, update_fields=("inventory_movement",))


class Migration(migrations.Migration):
    dependencies = [
        ("purchase", "0015_goods_receipt_idempotency"),
        ("inventory", "0005_retire_legacy_purchase_models_state"),
    ]

    operations = [
        migrations.AddField(
            model_name="goodsreceiptitem",
            name="inventory_movement",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="goods_receipt_items",
                to="inventory.inventoryv1stockmovement",
            ),
        ),
        migrations.RunPython(
            backfill_receipt_movement_links,
            migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="goodsreceiptitem",
            constraint=models.UniqueConstraint(
                condition=models.Q(inventory_movement__isnull=False),
                fields=("inventory_movement",),
                name="pur_gr_item_movement_uq",
            ),
        ),
    ]
