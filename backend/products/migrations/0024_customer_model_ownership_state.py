import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("customer", "0001_customer_model_ownership"),
        ("products", "0023_order_inventory_tracking_mode"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name="Customer"),
                migrations.AlterField(
                    model_name="order",
                    name="customer",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="orders",
                        to="customer.customer",
                    ),
                ),
                migrations.AlterField(
                    model_name="customeraccount",
                    name="customer",
                    field=models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="account",
                        to="customer.customer",
                    ),
                ),
                migrations.AlterField(
                    model_name="orderrefund",
                    name="customer",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="order_refunds",
                        to="customer.customer",
                    ),
                ),
            ],
        ),
    ]
