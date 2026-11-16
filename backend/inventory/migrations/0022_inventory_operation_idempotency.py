from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [("inventory", "0021_inventory_stock_movement_truncate_guard")]

    operations = [
        migrations.AddField(
            model_name="inventoryoperation",
            name="idempotency_key",
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="inventoryoperation",
            name="payload_fingerprint",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddConstraint(
            model_name="inventoryoperation",
            constraint=models.UniqueConstraint(
                condition=Q(idempotency_key__isnull=False),
                fields=("business", "idempotency_key"),
                name="inv_op_create_key_uq",
            ),
        ),
        migrations.AddConstraint(
            model_name="inventoryoperation",
            constraint=models.CheckConstraint(
                condition=(
                    Q(idempotency_key__isnull=True, payload_fingerprint__isnull=True)
                    | Q(idempotency_key__isnull=False, payload_fingerprint__isnull=False)
                ),
                name="inv_op_idempotency_pair_ck",
            ),
        ),
    ]
