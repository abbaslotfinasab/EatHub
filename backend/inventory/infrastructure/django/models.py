from decimal import Decimal

from django.db import models
from django.db.models import Q

from inventory.domain.enums.movement import MovementDirection, MovementType
from inventory.domain.value_objects.unit import Unit


class InventoryV1Stock(models.Model):
    """V1 authoritative stock projection, separate from the legacy Stock table."""

    business = models.ForeignKey(
        "accounts.Business",
        on_delete=models.PROTECT,
        related_name="inventory_v1_stocks",
    )
    warehouse = models.ForeignKey(
        "inventory.Warehouse",
        on_delete=models.PROTECT,
        related_name="inventory_v1_stocks",
    )
    ingredient = models.ForeignKey(
        "inventory.Ingredient",
        on_delete=models.PROTECT,
        related_name="inventory_v1_stocks",
    )
    unit = models.CharField(
        max_length=2,
        choices=[(item.value, item.value) for item in Unit],
    )
    quantity = models.DecimalField(
        max_digits=36,
        decimal_places=12,
        default=Decimal("0"),
    )
    average_cost = models.DecimalField(
        max_digits=70,
        decimal_places=48,
        default=Decimal("0"),
    )
    reorder_level = models.DecimalField(
        max_digits=36,
        decimal_places=12,
        default=Decimal("0"),
    )
    reorder_quantity = models.DecimalField(
        max_digits=36,
        decimal_places=12,
        default=Decimal("0"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory_v1_stock"
        constraints = [
            models.UniqueConstraint(
                fields=("business", "warehouse", "ingredient"),
                name="inv_v1_stock_key_uq",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gte=0), name="inv_v1_stock_qty_nonneg_ck"
            ),
            models.CheckConstraint(
                condition=Q(average_cost__gte=0), name="inv_v1_stock_cost_nonneg_ck"
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
                condition=Q(unit__in=[item.value for item in Unit]),
                name="inv_v1_stock_unit_ck",
            ),
        ]


class InventoryV1StockMovement(models.Model):
    """Append-only V1 movement history; edits are not exposed by repositories."""

    business = models.ForeignKey(
        "accounts.Business",
        on_delete=models.PROTECT,
        related_name="inventory_v1_movements",
    )
    stock = models.ForeignKey(
        InventoryV1Stock,
        on_delete=models.PROTECT,
        related_name="movements",
    )
    movement_type = models.CharField(
        max_length=20,
        choices=[(item.value, item.name.title()) for item in MovementType],
    )
    direction = models.CharField(
        max_length=3,
        choices=[(item.value, item.name.title()) for item in MovementDirection],
    )
    quantity = models.DecimalField(max_digits=36, decimal_places=12)
    unit = models.CharField(
        max_length=2,
        choices=[(item.value, item.value) for item in Unit],
    )
    unit_cost = models.DecimalField(max_digits=70, decimal_places=48)
    balance_after = models.DecimalField(max_digits=36, decimal_places=12)
    average_cost_before = models.DecimalField(max_digits=70, decimal_places=48)

    source_type = models.CharField(max_length=255)
    source_document_id = models.PositiveBigIntegerField()
    source_line_id = models.PositiveBigIntegerField()
    operation_kind = models.CharField(max_length=255)

    actor_id = models.PositiveBigIntegerField(null=True, blank=True)
    reason = models.TextField(null=True, blank=True)
    reverses_source_type = models.CharField(max_length=255, null=True, blank=True)
    reverses_source_document_id = models.PositiveBigIntegerField(null=True, blank=True)
    reverses_source_line_id = models.PositiveBigIntegerField(null=True, blank=True)
    reverses_operation_kind = models.CharField(max_length=255, null=True, blank=True)
    occurred_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inventory_v1_stock_movement"
        ordering = ("id",)
        constraints = [
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
                fields=(
                    "business",
                    "reverses_source_type",
                    "reverses_source_document_id",
                    "reverses_source_line_id",
                    "reverses_operation_kind",
                ),
                condition=Q(movement_type=MovementType.REVERSAL.value),
                name="inv_v1_move_reverse_uq",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gt=0), name="inv_v1_move_qty_positive_ck"
            ),
            models.CheckConstraint(
                condition=Q(balance_after__gte=0),
                name="inv_v1_move_balance_nonneg_ck",
            ),
            models.CheckConstraint(
                condition=Q(unit_cost__gte=0), name="inv_v1_move_unit_cost_ck"
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
                condition=Q(source_document_id__gt=0) & Q(source_line_id__gt=0),
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
                condition=Q(unit__in=[unit.value for unit in Unit]),
                name="inv_v1_move_unit_ck",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        movement_type=MovementType.REVERSAL.value,
                        reverses_source_type__gt="",
                        reverses_source_document_id__gt=0,
                        reverses_source_line_id__gt=0,
                        reverses_operation_kind__gt="",
                    )
                    | (
                        ~Q(movement_type=MovementType.REVERSAL.value)
                        & Q(reverses_source_type__isnull=True)
                        & Q(reverses_source_document_id__isnull=True)
                        & Q(reverses_source_line_id__isnull=True)
                        & Q(reverses_operation_kind__isnull=True)
                    )
                ),
                name="inv_v1_move_reverse_ref_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=("business", "stock", "id"),
                name="inv_v1_move_stock_order_ix",
            ),
        ]
