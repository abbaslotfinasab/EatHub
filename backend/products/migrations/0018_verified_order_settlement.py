from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0017_order_refund_audit"),
    ]

    operations = [
        migrations.AddField(
            model_name="customertransaction",
            name="is_order_settlement_verified",
            field=models.BooleanField(default=False),
        ),
    ]
