from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("purchase", "0018_payment_allocation_idempotency"),
    ]

    operations = [
        migrations.AddField(
            model_name="supplierpayment",
            name="idempotency_key",
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="supplierpayment",
            name="payload_fingerprint",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name="supplierpayment",
            name="payload_version",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddConstraint(
            model_name="supplierpayment",
            constraint=models.UniqueConstraint(
                fields=("business", "idempotency_key"),
                name="pur_sp_business_idem_uq",
            ),
        ),
        migrations.AddConstraint(
            model_name="supplierpayment",
            constraint=models.CheckConstraint(
                condition=(
                    Q(
                        idempotency_key__isnull=True,
                        payload_fingerprint__isnull=True,
                        payload_version__isnull=True,
                    )
                    | Q(
                        idempotency_key__isnull=False,
                        payload_fingerprint__isnull=False,
                        payload_version__isnull=False,
                        payload_version__gte=1,
                    )
                ),
                name="pur_sp_key_fp_pair_ck",
            ),
        ),
    ]
