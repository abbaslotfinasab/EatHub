from django.db import migrations, models
import django.db.models.deletion


def backfill_receipt_movement_links(apps, schema_editor):
    GoodsReceiptItem = apps.get_model("purchase", "GoodsReceiptItem")
    Link = apps.get_model("purchase", "GoodsReceiptInventoryMovementLink")
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
        if line is not None:
            Link.objects.using(database).get_or_create(
                receipt_item_id=line.pk,
                defaults={"movement_id": movement.pk},
            )


class Migration(migrations.Migration):
    dependencies = [
        ("purchase", "0015_goods_receipt_idempotency"),
        ("inventory", "0005_retire_legacy_purchase_models_state"),
    ]

    operations = [
        migrations.CreateModel(
            name="GoodsReceiptInventoryMovementLink",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "movement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="goods_receipt_links",
                        to="inventory.inventoryv1stockmovement",
                    ),
                ),
                (
                    "receipt_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="inventory_movement_links",
                        to="purchase.goodsreceiptitem",
                    ),
                ),
            ],
            options={
                "db_table": "purchase_goods_receipt_inventory_movement",
            },
        ),
        migrations.AddConstraint(
            model_name="goodsreceiptinventorymovementlink",
            constraint=models.UniqueConstraint(
                fields=("receipt_item",),
                name="pur_gr_link_receipt_item_uq",
            ),
        ),
        migrations.AddConstraint(
            model_name="goodsreceiptinventorymovementlink",
            constraint=models.UniqueConstraint(
                fields=("movement",),
                name="pur_gr_link_movement_uq",
            ),
        ),
        migrations.RunPython(
            backfill_receipt_movement_links,
            migrations.RunPython.noop,
        ),
    ]
