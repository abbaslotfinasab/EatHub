from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0012_inventory_reservations"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="inventoryreservation",
            constraint=models.CheckConstraint(
                condition=Q(status__in=("active", "released")),
                name="inv_res_status_ck",
            ),
        ),
    ]
