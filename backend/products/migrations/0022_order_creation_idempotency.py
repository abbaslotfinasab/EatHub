import django.db.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0021_order_inventory_requirements"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="idempotency_key",
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="payload_fingerprint",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddConstraint(
            model_name="order",
            constraint=models.UniqueConstraint(
                condition=models.Q(idempotency_key__isnull=False),
                fields=("business", "idempotency_key"),
                name="order_business_idem_key_uq",
            ),
        ),
    ]
