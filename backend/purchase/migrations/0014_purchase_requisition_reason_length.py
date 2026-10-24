from django.db import migrations, models
from django.db.models.functions import Length
from django.db.models.lookups import LessThanOrEqual


class Migration(migrations.Migration):
    dependencies = [
        ("purchase", "0013_purchaserequisitiondecision"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="purchaserequisitiondecision",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(rejection_reason__isnull=True)
                    | models.Q(
                        LessThanOrEqual(Length("rejection_reason"), 2000)
                    )
                ),
                name="pur_req_reason_len_ck",
            ),
        ),
    ]
