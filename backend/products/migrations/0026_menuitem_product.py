import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
        ("products", "0025_financial_model_ownership_state"),
    ]

    operations = [
        migrations.AddField(
            model_name="menuitem",
            name="product",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="menu_items",
                to="catalog.product",
            ),
        ),
    ]
