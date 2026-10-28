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
                    | Q(movement_type="issue", direction="out")
                    | Q(movement_type="transfer_dispatch", direction="out")
                    | Q(movement_type="transfer_receipt", direction="in")
                    | Q(movement_type="adjustment", direction__in=("in", "out"))
                    | Q(movement_type="reversal", direction__in=("in", "out"))
                    | Q(movement_type=MovementType.OPENING_BALANCE.value, direction=MovementDirection.IN.value)
                ),
                name="inv_v1_move_type_dir_ck",
            ),
            models.CheckConstraint(
                condition=(
                    ~Q(movement_type=MovementType.ISSUE.value)
                    | (Q(reason__gt="") & Q(actor_id__isnull=False))
                ),
                name="inv_v1_issue_audit_ck",
            ),
            models.CheckConstraint(
                condition=(
                    ~Q(movement_type__in=(MovementType.TRANSFER_DISPATCH.value, MovementType.TRANSFER_RECEIPT.value))
                    | Q(actor_id__isnull=False)
                ),
                name="inv_v1_transfer_actor_ck",
            ),
            models.CheckConstraint(
                condition=(~Q(movement_type=MovementType.OPENING_BALANCE.value) | Q(actor_id__isnull=False)),
                name="inv_v1_opening_actor_ck",
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


class InventoryOperation(models.Model):
    """Business-scoped workflow document; stock truth remains in the V1 ledger."""

    class Type(models.TextChoices):
        ISSUE = "issue", "Issue"
        TRANSFER = "transfer", "Transfer"
        STOCKTAKE = "stocktake", "Stocktake"
        OPENING_STOCK = "opening_stock", "Opening stock"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        IN_TRANSIT = "in_transit", "In transit"
        POSTED = "posted", "Posted"
        RECEIVED = "received", "Received"
        APPROVED = "approved", "Approved"
        REVERSED = "reversed", "Reversed"
        CANCELLED = "cancelled", "Cancelled"

    business = models.ForeignKey("accounts.Business", on_delete=models.PROTECT)
    operation_type = models.CharField(max_length=16, choices=Type.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    warehouse = models.ForeignKey("inventory.Warehouse", on_delete=models.PROTECT, related_name="inventory_operations_from")
    destination_warehouse = models.ForeignKey("inventory.Warehouse", on_delete=models.PROTECT, null=True, blank=True, related_name="inventory_operations_to")
    reference = models.CharField(max_length=120, blank=True)
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_by_id = models.PositiveBigIntegerField()
    completed_by_id = models.PositiveBigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "inventory_operation"
        ordering = ("-created_at", "-id")
        indexes = [models.Index(fields=("business", "operation_type", "status", "id"), name="inv_operation_scope_ix")]
        constraints = [
            models.CheckConstraint(condition=Q(operation_type="transfer", destination_warehouse__isnull=False) | ~Q(operation_type="transfer"), name="inv_op_transfer_dest_ck"),
            models.CheckConstraint(condition=Q(operation_type="transfer") | Q(destination_warehouse__isnull=True), name="inv_op_no_dest_ck"),
            models.CheckConstraint(
                condition=(
                    Q(operation_type="issue", status__in=("draft", "posted", "reversed", "cancelled"))
                    | Q(operation_type="transfer", status__in=("draft", "in_transit", "received", "cancelled"))
                    | Q(operation_type="stocktake", status__in=("draft", "approved", "cancelled"))
                    | Q(operation_type="opening_stock", status__in=("posted", "cancelled"))
                ),
                name="inv_op_state_ck",
            ),
        ]


class InventoryOperationLine(models.Model):
    operation = models.ForeignKey(InventoryOperation, on_delete=models.PROTECT, related_name="lines")
    ingredient = models.ForeignKey("inventory.Ingredient", on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=36, decimal_places=12)
    unit = models.CharField(max_length=2, choices=[(item.value, item.value) for item in Unit])
    system_quantity = models.DecimalField(max_digits=36, decimal_places=12, null=True, blank=True)
    counted_quantity = models.DecimalField(max_digits=36, decimal_places=12, null=True, blank=True)
    counted_unit_cost = models.DecimalField(max_digits=70, decimal_places=48, null=True, blank=True)
    counted_by_id = models.PositiveBigIntegerField(null=True, blank=True)
    counted_at = models.DateTimeField(null=True, blank=True)
    snapshot_movement_id = models.PositiveBigIntegerField(null=True, blank=True)
    transfer_unit_cost = models.DecimalField(max_digits=70, decimal_places=48, null=True, blank=True)

    class Meta:
        db_table = "inventory_operation_line"
        constraints = [
            models.UniqueConstraint(fields=("operation", "ingredient"), name="inv_operation_item_uq"),
            models.CheckConstraint(condition=Q(quantity__gte=0), name="inv_operation_qty_nonneg_ck"),
            models.CheckConstraint(condition=Q(counted_quantity__isnull=True) | Q(counted_quantity__gte=0), name="inv_operation_count_nonneg_ck"),
            models.CheckConstraint(condition=Q(system_quantity__isnull=True) | Q(system_quantity__gte=0), name="inv_op_snapshot_ck"),
            models.CheckConstraint(condition=Q(counted_unit_cost__isnull=True) | Q(counted_unit_cost__gte=0), name="inv_op_count_cost_ck"),
            models.CheckConstraint(condition=Q(transfer_unit_cost__isnull=True) | Q(transfer_unit_cost__gte=0), name="inv_op_transfer_cost_ck"),
        ]


class InventoryReservation(models.Model):
    """An auditable availability hold; it never changes physical stock."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        RELEASED = "released", "Released"

    business = models.ForeignKey(
        "accounts.Business", on_delete=models.PROTECT, related_name="inventory_reservations"
    )
    warehouse = models.ForeignKey(
        "inventory.Warehouse", on_delete=models.PROTECT, related_name="inventory_reservations"
    )
    source_type = models.CharField(max_length=64)
    source_id = models.PositiveBigIntegerField(null=True, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    idempotency_key = models.UUIDField()
    payload_fingerprint = models.CharField(max_length=64)
    created_by_id = models.PositiveBigIntegerField()
    released_by_id = models.PositiveBigIntegerField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    release_idempotency_key = models.UUIDField(null=True, blank=True)
    release_reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory_reservation"
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=("business", "status", "id"), name="inv_res_scope_status_ix"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("business", "idempotency_key"), name="inv_res_create_key_uq"
            ),
            models.UniqueConstraint(
                fields=("business", "release_idempotency_key"),
                condition=Q(release_idempotency_key__isnull=False),
                name="inv_res_release_key_uq",
            ),
            models.UniqueConstraint(
                fields=("business", "source_type", "source_id"),
                condition=Q(status="active", source_id__isnull=False),
                name="inv_res_active_source_uq",
            ),
            models.CheckConstraint(
                condition=Q(source_type__gt=""), name="inv_res_source_type_ck"
            ),
            models.CheckConstraint(
                condition=Q(status__in=("active", "released")),
                name="inv_res_status_ck",
            ),
            models.CheckConstraint(
                condition=Q(reason__gt=""), name="inv_res_reason_ck"
            ),
            models.CheckConstraint(
                condition=Q(source_id__isnull=True) | Q(source_id__gt=0),
                name="inv_res_source_id_ck",
            ),
            models.CheckConstraint(
                condition=Q(created_by_id__gt=0), name="inv_res_created_actor_ck"
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        status="active", released_by_id__isnull=True,
                        released_at__isnull=True, release_idempotency_key__isnull=True,
                        release_reason="",
                    )
                    | Q(
                        status="released", released_by_id__gt=0,
                        released_at__isnull=False,
                        release_idempotency_key__isnull=False,
                        release_reason__gt="",
                    )
                ),
                name="inv_res_release_state_ck",
            ),
        ]


class InventoryReservationLine(models.Model):
    reservation = models.ForeignKey(
        InventoryReservation, on_delete=models.PROTECT, related_name="lines"
    )
    ingredient = models.ForeignKey(
        "inventory.Ingredient", on_delete=models.PROTECT, related_name="inventory_reservation_lines"
    )
    source_line_id = models.PositiveBigIntegerField(null=True, blank=True)
    quantity = models.DecimalField(max_digits=36, decimal_places=12)
    unit = models.CharField(max_length=2, choices=[(item.value, item.value) for item in Unit])

    class Meta:
        db_table = "inventory_reservation_line"
        constraints = [
            models.UniqueConstraint(
                fields=("reservation", "source_line_id"),
                condition=Q(source_line_id__isnull=False),
                name="inv_res_line_source_uq",
            ),
            models.UniqueConstraint(
                fields=("reservation", "ingredient"),
                condition=Q(source_line_id__isnull=True),
                name="inv_res_line_item_uq",
            ),
            models.CheckConstraint(
                condition=Q(source_line_id__isnull=True) | Q(source_line_id__gt=0),
                name="inv_res_line_source_id_ck",
            ),
            models.CheckConstraint(
                condition=(
                    Q(quantity__gt=0)
                    & Q(quantity__lte=Decimal("999999999999999999999999.999999999999"))
                ),
                name="inv_res_line_qty_ck",
            ),
            models.CheckConstraint(
                condition=Q(unit__in=[item.value for item in Unit]),
                name="inv_res_line_unit_ck",
            ),
        ]
