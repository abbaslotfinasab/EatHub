import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0014_order_lifecycle_permissions"),
        ("inventory", "0013_reservation_status_constraint"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="LegacyPurchaseOrder",
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
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        ("supplier_id", models.CharField(blank=True, max_length=64, null=True)),
                        ("supplier_name", models.CharField(max_length=150)),
                        ("supplier_number", models.CharField(blank=True, default="", max_length=30)),
                        (
                            "type",
                            models.CharField(
                                choices=[("purchase", "Purchase"), ("sales", "Sales")],
                                default="purchase",
                                max_length=20,
                            ),
                        ),
                        (
                            "status",
                            models.CharField(
                                choices=[
                                    ("draft", "Draft"),
                                    ("ordered", "Ordered"),
                                    ("partially_received", "Partially Received"),
                                    ("received", "Received"),
                                    ("cancelled", "Cancelled"),
                                ],
                                default="draft",
                                max_length=30,
                            ),
                        ),
                        ("subtotal", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                        ("discount", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                        ("tax", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                        ("total_amount", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                        ("invoice_number", models.CharField(blank=True, max_length=100, null=True)),
                        ("notes", models.TextField(blank=True, null=True)),
                        (
                            "business",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="purchase_orders",
                                to="accounts.business",
                            ),
                        ),
                    ],
                    options={
                        "db_table": "inventory_purchaseorder",
                        "ordering": ["-created_at"],
                    },
                ),
                migrations.CreateModel(
                    name="LegacyPurchaseOrderItem",
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
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        (
                            "item_type",
                            models.CharField(
                                choices=[("ingredient", "Ingredient"), ("menu_item", "Menu Item")],
                                max_length=20,
                            ),
                        ),
                        ("item_id", models.PositiveIntegerField()),
                        ("quantity", models.DecimalField(decimal_places=3, max_digits=12)),
                        ("unit_price", models.DecimalField(decimal_places=2, max_digits=12)),
                        ("total_price", models.DecimalField(decimal_places=2, max_digits=12)),
                        (
                            "purchase_order",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="items",
                                to="inventory.legacypurchaseorder",
                            ),
                        ),
                    ],
                    options={
                        "db_table": "inventory_purchaseorderitem",
                        "ordering": ["id"],
                    },
                ),
            ],
        ),
    ]
