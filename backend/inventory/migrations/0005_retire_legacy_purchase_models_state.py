from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0004_inventory_v1_persistence"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                # Remove the child model first because it references PurchaseOrder.
                migrations.DeleteModel(name="PurchaseOrderItem"),
                migrations.DeleteModel(name="PurchaseOrder"),
            ],
        ),
    ]
