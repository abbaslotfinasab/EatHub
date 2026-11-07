from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0022_order_creation_idempotency"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="inventory_tracking_enabled",
            field=models.BooleanField(blank=True, default=None, null=True),
        ),
    ]
