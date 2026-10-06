import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("purchase", "0006_purchase_invoice_item_po_item_and_matching"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AccountsPayable",
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
                ("amount", models.DecimalField(decimal_places=2, max_digits=14)),
                ("due_date", models.DateField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("open", "Open"),
                            ("partially_paid", "Partially paid"),
                            ("paid", "Paid"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="open",
                        max_length=20,
                    ),
                ),
                ("posted_at", models.DateTimeField(blank=True, null=True)),
                ("cancelled_at", models.DateTimeField(blank=True, null=True)),
                ("cancellation_reason", models.TextField(blank=True, default="")),
                (
                    "business",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="accounts_payables",
                        to="accounts.business",
                    ),
                ),
                (
                    "cancelled_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="cancelled_accounts_payables",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "posted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="posted_accounts_payables",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "source_invoice",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="accounts_payable",
                        to="purchase.purchaseinvoice",
                    ),
                ),
                (
                    "supplier",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="accounts_payables",
                        to="purchase.supplier",
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("amount__gt", 0)),
                        name="purchase_accounts_payable_amount_positive",
                    ),
                ],
            },
        ),
    ]
