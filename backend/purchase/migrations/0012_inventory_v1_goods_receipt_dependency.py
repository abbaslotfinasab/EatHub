from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("purchase", "0011_goods_receipt_inventory_units"),
        ("inventory", "0005_retire_legacy_purchase_models_state"),
    ]

    operations = []
