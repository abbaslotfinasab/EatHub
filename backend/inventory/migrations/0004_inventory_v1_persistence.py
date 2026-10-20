from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0008_remove_business_qr_code"),
        ("inventory", "0003_add_stocktransaction_balance_after"),
    ]

    operations = [
        migrations.CreateModel(
            name="InventoryV1Stock",
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
                    "unit",
                    models.CharField(
                        choices=[
                            ("kg", "kg"),
                            ("g", "g"),
                            ("l", "l"),
                            ("ml", "ml"),
                            ("pc", "pc"),
                            ("pk", "pk"),
                        ],
                        max_length=2,
                    ),
                ),
                (
                    "quantity",
                    models.DecimalField(
                        decimal_places=12, default=Decimal("0"), max_digits=36
                    ),
                ),
                (
                    "average_cost",
                    models.DecimalField(
                        decimal_places=48, default=Decimal("0"), max_digits=70
                    ),
                ),
                (
                    "reorder_level",
                    models.DecimalField(
                        decimal_places=12, default=Decimal("0"), max_digits=36
                    ),
                ),
                (
                    "reorder_quantity",
                    models.DecimalField(
                        decimal_places=12, default=Decimal("0"), max_digits=36
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "business",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="inventory_v1_stocks",
                        to="accounts.business",
                    ),
                ),
                (
                    "ingredient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="inventory_v1_stocks",
                        to="inventory.ingredient",
                    ),
                ),
                (
                    "warehouse",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="inventory_v1_stocks",
                        to="inventory.warehouse",
                    ),
                ),
            ],
            options={
                "db_table": "inventory_v1_stock",
                "constraints": [
                    models.UniqueConstraint(
                        fields=("business", "warehouse", "ingredient"),
                        name="inv_v1_stock_key_uq",
                    ),
                    models.CheckConstraint(
                        condition=Q(quantity__gte=0),
                        name="inv_v1_stock_qty_nonneg_ck",
                    ),
                    models.CheckConstraint(
                        condition=Q(average_cost__gte=0),
                        name="inv_v1_stock_cost_nonneg_ck",
                    ),
                    models.CheckConstraint(
                        condition=Q(reorder_level__gte=0),
                        name="inv_v1_stock_reorder_level_ck",
                    ),
                    models.CheckConstraint(
                        condition=Q(reorder_quantity__gte=0),
                        name="inv_v1_stock_reorder_qty_ck",
                    ),
                    models.CheckConstraint(
                        condition=Q(unit__in=["kg", "g", "l", "ml", "pc", "pk"]),
                        name="inv_v1_stock_unit_ck",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="InventoryV1StockMovement",
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
                    "movement_type",
                    models.CharField(
                        choices=[
                            ("receipt", "Receipt"),
                            ("adjustment", "Adjustment"),
                            ("reversal", "Reversal"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "direction",
                    models.CharField(
                        choices=[("in", "In"), ("out", "Out")], max_length=3
                    ),
                ),
                (
                    "quantity",
                    models.DecimalField(decimal_places=12, max_digits=36),
                ),
                (
                    "unit",
                    models.CharField(
                        choices=[
                            ("kg", "kg"),
                            ("g", "g"),
                            ("l", "l"),
                            ("ml", "ml"),
                            ("pc", "pc"),
                            ("pk", "pk"),
                        ],
                        max_length=2,
                    ),
                ),
                (
                    "unit_cost",
                    models.DecimalField(decimal_places=48, max_digits=70),
                ),
                (
                    "balance_after",
                    models.DecimalField(decimal_places=12, max_digits=36),
                ),
                (
                    "average_cost_before",
                    models.DecimalField(decimal_places=48, max_digits=70),
                ),
                ("source_type", models.CharField(max_length=255)),
                ("source_document_id", models.PositiveBigIntegerField()),
                ("source_line_id", models.PositiveBigIntegerField()),
                ("operation_kind", models.CharField(max_length=255)),
                (
                    "actor_id",
                    models.PositiveBigIntegerField(blank=True, null=True),
                ),
                ("reason", models.TextField(blank=True, null=True)),
                (
                    "reverses_source_type",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "reverses_source_document_id",
                    models.PositiveBigIntegerField(blank=True, null=True),
                ),
                (
                    "reverses_source_line_id",
                    models.PositiveBigIntegerField(blank=True, null=True),
                ),
                (
                    "reverses_operation_kind",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "occurred_at",
                    models.DateTimeField(blank=True, null=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "business",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="inventory_v1_movements",
                        to="accounts.business",
                    ),
                ),
                (
                    "stock",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="movements",
                        to="inventory.inventoryv1stock",
                    ),
                ),
            ],
            options={
                "db_table": "inventory_v1_stock_movement",
                "ordering": ("id",),
                "constraints": [
                    models.UniqueConstraint(
                        fields=(
                            "business",
                            "source_type",
                            "source_document_id",
                            "source_line_id",
                            "operation_kind",
                        ),
                        name="inv_v1_move_source_uq",
                    ),
                    models.UniqueConstraint(
                        condition=Q(movement_type="reversal"),
                        fields=(
                            "business",
                            "reverses_source_type",
                            "reverses_source_document_id",
                            "reverses_source_line_id",
                            "reverses_operation_kind",
                        ),
                        name="inv_v1_move_reverse_uq",
                    ),
                    models.CheckConstraint(
                        condition=Q(quantity__gt=0),
                        name="inv_v1_move_qty_positive_ck",
                    ),
                    models.CheckConstraint(
                        condition=Q(balance_after__gte=0),
                        name="inv_v1_move_balance_nonneg_ck",
                    ),
                    models.CheckConstraint(
                        condition=Q(unit_cost__gte=0),
                        name="inv_v1_move_unit_cost_ck",
                    ),
                    models.CheckConstraint(
                        condition=Q(average_cost_before__gte=0),
                        name="inv_v1_move_avg_before_ck",
                    ),
                    models.CheckConstraint(
                        condition=Q(source_type__gt="") & Q(operation_kind__gt=""),
                        name="inv_v1_move_source_text_ck",
                    ),
                    models.CheckConstraint(
                        condition=Q(source_document_id__gt=0)
                        & Q(source_line_id__gt=0),
                        name="inv_v1_move_source_ids_ck",
                    ),
                    models.CheckConstraint(
                        condition=Q(actor_id__isnull=True) | Q(actor_id__gt=0),
                        name="inv_v1_move_actor_ck",
                    ),
                    models.CheckConstraint(
                        condition=(
                            Q(movement_type="receipt", direction="in")
                            | Q(movement_type="adjustment", direction__in=("in", "out"))
                            | Q(movement_type="reversal", direction__in=("in", "out"))
                        ),
                        name="inv_v1_move_type_dir_ck",
                    ),
                    models.CheckConstraint(
                        condition=Q(unit__in=["kg", "g", "l", "ml", "pc", "pk"]),
                        name="inv_v1_move_unit_ck",
                    ),
                    models.CheckConstraint(
                        condition=(
                            Q(
                                movement_type="reversal",
                                reverses_source_type__gt="",
                                reverses_source_document_id__gt=0,
                                reverses_source_line_id__gt=0,
                                reverses_operation_kind__gt="",
                            )
                            | (
                                ~Q(movement_type="reversal")
                                & Q(reverses_source_type__isnull=True)
                                & Q(reverses_source_document_id__isnull=True)
                                & Q(reverses_source_line_id__isnull=True)
                                & Q(reverses_operation_kind__isnull=True)
                            )
                        ),
                        name="inv_v1_move_reverse_ref_ck",
                    ),
                ],
                "indexes": [
                    models.Index(
                        fields=["business", "stock", "id"],
                        name="inv_v1_move_stock_order_ix",
                    ),
                ],
            },
        ),
    ]
