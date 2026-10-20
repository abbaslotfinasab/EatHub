from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("purchase", "0010_purchaseinvoice_cancellation")]

    operations = [
        migrations.AddField(
            model_name="purchaseorderitem",
            name="purchase_unit",
            field=models.CharField(
                blank=True,
                choices=[("kg", "kg"), ("g", "g"), ("l", "l"), ("ml", "ml"), ("pc", "pc")],
                max_length=2,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="goodsreceiptitem",
            name="purchase_unit",
            field=models.CharField(
                blank=True,
                choices=[("kg", "kg"), ("g", "g"), ("l", "l"), ("ml", "ml"), ("pc", "pc")],
                max_length=2,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="goodsreceipt",
            name="warehouse_id",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
    ]
