import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


MODEL_NAMES = ("customeraccount", "orderrefund", "customertransaction")


def move_financial_content_types(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    manager = ContentType.objects.using(schema_editor.connection.alias)
    for model_name in MODEL_NAMES:
        old_exists = manager.filter(app_label="products", model=model_name).exists()
        new_exists = manager.filter(app_label="financial", model=model_name).exists()
        if old_exists and new_exists:
            raise RuntimeError(
                f"Both products.{model_name} and financial.{model_name} content types exist; "
                "reconcile permissions and generic references before migrating."
            )
    for model_name in MODEL_NAMES:
        old = manager.filter(app_label="products", model=model_name).first()
        if old is not None:
            old.app_label = "financial"
            old.save(update_fields=["app_label"])


def reverse_financial_content_types(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    manager = ContentType.objects.using(schema_editor.connection.alias)
    for model_name in MODEL_NAMES:
        old_exists = manager.filter(app_label="products", model=model_name).exists()
        new_exists = manager.filter(app_label="financial", model=model_name).exists()
        if old_exists and new_exists:
            raise RuntimeError(
                f"Both products.{model_name} and financial.{model_name} content types exist; "
                "manual reconciliation is required before reversing."
            )
    for model_name in MODEL_NAMES:
        current = manager.filter(app_label="financial", model=model_name).first()
        if current is not None:
            current.app_label = "products"
            current.save(update_fields=["app_label"])


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("customer", "0001_customer_model_ownership"),
        ("products", "0024_customer_model_ownership_state"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="CustomerAccount",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        ("balance", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                        ("ledger_opening_balance", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                        ("ledger_opening_balance_verified", models.BooleanField(default=False)),
                        ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="accounts.business")),
                        ("customer", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="account", to="customer.customer")),
                    ],
                    options={"db_table": "products_customeraccount"},
                ),
                migrations.CreateModel(
                    name="OrderRefund",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        ("payment_method", models.CharField(choices=[("cash", "Cash"), ("card", "Card"), ("customer_account", "Customer Account")], max_length=30)),
                        ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                        ("reason", models.TextField()),
                        ("reference", models.CharField(blank=True, max_length=200)),
                        ("idempotency_key", models.UUIDField(unique=True)),
                        ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="order_refunds", to=settings.AUTH_USER_MODEL)),
                        ("business", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_refunds", to="accounts.business")),
                        ("customer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="order_refunds", to="customer.customer")),
                        ("order", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="refunds", to="products.order")),
                    ],
                    options={
                        "db_table": "products_orderrefund",
                        "constraints": [
                            models.CheckConstraint(condition=models.Q(("amount__gt", 0)), name="order_refund_positive_amt"),
                        ],
                    },
                ),
                migrations.CreateModel(
                    name="CustomerTransaction",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        ("type", models.CharField(choices=[("credit", "Credit"), ("debit", "Debit"), ("adjust", "Adjust")], max_length=10)),
                        ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                        ("balance_after", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                        ("is_order_settlement", models.BooleanField(default=False)),
                        ("is_order_settlement_verified", models.BooleanField(default=False)),
                        ("description", models.TextField(blank=True, null=True)),
                        ("account", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="transactions", to="financial.customeraccount")),
                        ("order", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="products.order")),
                        ("refund", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="transactions", to="financial.orderrefund")),
                    ],
                    options={
                        "db_table": "products_customertransaction",
                        "constraints": [
                            models.UniqueConstraint(condition=models.Q(("refund__isnull", False)), fields=("refund",), name="uniq_txn_refund"),
                        ],
                    },
                ),
            ],
        ),
        migrations.RunPython(
            move_financial_content_types,
            reverse_financial_content_types,
        ),
    ]
