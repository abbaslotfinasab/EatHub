from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0026_menuitem_product"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderitem",
            name="catalog_product_id",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="catalog_product_name",
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
    ]
