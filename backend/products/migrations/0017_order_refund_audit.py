import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


def grant_payment_management(apps, schema_editor):
    Permission = apps.get_model("accounts", "Permission")
    Role = apps.get_model("accounts", "Role")
    RolePermission = apps.get_model("accounts", "RolePermission")
    db = schema_editor.connection.alias

    permission, _ = Permission.objects.using(db).get_or_create(
        code="payments.manage",
        defaults={"name": "Manage Payments and Refunds"},
    )
    roles = Role.objects.using(db).filter(code__in=("OWNER", "MANAGER", "ACCOUNTANT"))
    for role in roles:
        RolePermission.objects.using(db).get_or_create(
            role_id=role.id,
            permission_id=permission.id,
        )


def revoke_payment_management(apps, schema_editor):
    # This migration may have found an existing shared Permission row and may
    # have found pre-existing role links. The schema has no provenance column
    # that can distinguish links created here from links that predated it, so a
    # downgrade deliberately preserves the shared RBAC data rather than
    # deleting assignments that may belong to the existing application.
    return None


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0008_remove_business_qr_code"),
        ("products", "0016_wallet_order_reconciliation"),
    ]

    operations = [
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
                ("customer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="order_refunds", to="products.customer")),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="refunds", to="products.order")),
            ],
            options={
                "constraints": [
                    models.CheckConstraint(condition=models.Q(("amount__gt", 0)), name="order_refund_positive_amt"),
                ],
            },
        ),
        migrations.AddField(
            model_name="customertransaction",
            name="refund",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="transactions", to="products.orderrefund"),
        ),
        migrations.AddConstraint(
            model_name="customertransaction",
            constraint=models.UniqueConstraint(
                fields=("refund",),
                condition=models.Q(("refund__isnull", False)),
                name="uniq_txn_refund",
            ),
        ),
        migrations.RunPython(grant_payment_management, revoke_payment_management),
    ]
