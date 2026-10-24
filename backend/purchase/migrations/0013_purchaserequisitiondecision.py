# Generated for the Purchase requisition decision history.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("purchase", "0012_inventory_v1_goods_receipt_dependency"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PurchaseRequisitionDecision",
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
                    "decision",
                    models.CharField(
                        choices=[("approved", "Approved"), ("rejected", "Rejected")],
                        max_length=10,
                    ),
                ),
                ("decided_at", models.DateTimeField(auto_now_add=True)),
                (
                    "previous_status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("submitted", "Submitted"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                            ("completed", "Completed"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "resulting_status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("submitted", "Submitted"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                            ("completed", "Completed"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "rejection_reason",
                    models.TextField(blank=True, null=True),
                ),
                (
                    "actor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="purchase_requisition_decisions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "requisition",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="decisions",
                        to="purchase.purchaserequisition",
                    ),
                ),
            ],
            options={"ordering": ["decided_at", "id"]},
        ),
        migrations.AddConstraint(
            model_name="purchaserequisitiondecision",
            constraint=models.UniqueConstraint(
                fields=("requisition",),
                name="pur_req_decision_uq",
            ),
        ),
        migrations.AddConstraint(
            model_name="purchaserequisitiondecision",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(
                        ("decision", "approved"),
                        ("previous_status", "submitted"),
                        ("resulting_status", "approved"),
                        ("rejection_reason__isnull", True),
                    )
                    | models.Q(
                        ("decision", "rejected"),
                        ("previous_status", "submitted"),
                        ("resulting_status", "rejected"),
                    )
                ),
                name="pur_req_decision_ck",
            ),
        ),
        # A rollback must not silently erase the only durable decision history.
        migrations.RunPython(migrations.RunPython.noop),
    ]
