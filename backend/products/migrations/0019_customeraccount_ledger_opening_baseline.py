from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0018_verified_order_settlement"),
    ]

    operations = [
        migrations.AddField(
            model_name="customeraccount",
            name="ledger_opening_balance",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0"),
                max_digits=12,
            ),
        ),
        migrations.AddField(
            model_name="customeraccount",
            name="ledger_opening_balance_verified",
            field=models.BooleanField(default=False),
        ),
    ]
