import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0017_default_order_view_permission"),
        ("products", "0027_orderitem_catalog_product_snapshot"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrderStatusHistory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "from_status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("pending", "Pending"),
                            ("confirmed", "Confirmed"),
                            ("preparing", "Preparing"),
                            ("ready", "Ready"),
                            ("completed", "Completed"),
                            ("cancelled", "Cancelled"),
                            ("failed", "Failed"),
                        ],
                        max_length=20,
                        null=True,
                    ),
                ),
                (
                    "to_status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("confirmed", "Confirmed"),
                            ("preparing", "Preparing"),
                            ("ready", "Ready"),
                            ("completed", "Completed"),
                            ("cancelled", "Cancelled"),
                            ("failed", "Failed"),
                        ],
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="order_status_changes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("order_id_snapshot", models.PositiveBigIntegerField()),
                (
                    "business",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="order_status_history",
                        to="accounts.business",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="status_history",
                        to="products.order",
                    ),
                ),
            ],
            options={
                "db_table": "order_status_history",
                "ordering": ("created_at", "pk"),
            },
        ),
        migrations.AddIndex(
            model_name="orderstatushistory",
            index=models.Index(
                fields=["business", "order_id_snapshot", "created_at"],
                name="order_status_hist_scope_ix",
            ),
        ),
    ]
