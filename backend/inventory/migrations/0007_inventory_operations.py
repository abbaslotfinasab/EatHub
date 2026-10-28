from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [("inventory", "0006_master_data_invariants")]

    operations = [
        migrations.AlterField(
            model_name="inventoryv1stockmovement",
            name="movement_type",
            field=models.CharField(
                choices=[("receipt", "Receipt"), ("issue", "Issue"), ("transfer_dispatch", "Transfer_Dispatch"), ("transfer_receipt", "Transfer_Receipt"), ("adjustment", "Adjustment"), ("reversal", "Reversal")],
                max_length=20,
            ),
        ),
        migrations.RemoveConstraint(
            model_name="inventoryv1stockmovement",
            name="inv_v1_move_type_dir_ck",
        ),
        migrations.AddConstraint(
            model_name="inventoryv1stockmovement",
            constraint=models.CheckConstraint(
                condition=(
                    Q(movement_type="receipt", direction="in")
                    | Q(movement_type="issue", direction="out")
                    | Q(movement_type="transfer_dispatch", direction="out")
                    | Q(movement_type="transfer_receipt", direction="in")
                    | Q(movement_type="adjustment", direction__in=("in", "out"))
                    | Q(movement_type="reversal", direction__in=("in", "out"))
                ),
                name="inv_v1_move_type_dir_ck",
            ),
        ),
        migrations.AddConstraint(
            model_name="inventoryv1stockmovement",
            constraint=models.CheckConstraint(
                condition=~Q(movement_type="issue") | (Q(reason__gt="") & Q(actor_id__isnull=False)),
                name="inv_v1_issue_audit_ck",
            ),
        ),
        migrations.AddConstraint(
            model_name="inventoryv1stockmovement",
            constraint=models.CheckConstraint(
                condition=~Q(movement_type__in=("transfer_dispatch", "transfer_receipt")) | Q(actor_id__isnull=False),
                name="inv_v1_transfer_actor_ck",
            ),
        ),
        migrations.CreateModel(
            name="InventoryOperation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("operation_type", models.CharField(choices=[("issue", "Issue"), ("transfer", "Transfer"), ("stocktake", "Stocktake")], max_length=16)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("in_transit", "In transit"), ("posted", "Posted"), ("received", "Received"), ("approved", "Approved"), ("reversed", "Reversed"), ("cancelled", "Cancelled")], default="draft", max_length=16)),
                ("reference", models.CharField(blank=True, max_length=120)),
                ("reason", models.TextField(blank=True)),
                ("notes", models.TextField(blank=True)),
                ("created_by_id", models.PositiveBigIntegerField()),
                ("completed_by_id", models.PositiveBigIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("business", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="accounts.business")),
                ("destination_warehouse", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="inventory_operations_to", to="inventory.warehouse")),
                ("warehouse", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="inventory_operations_from", to="inventory.warehouse")),
            ],
            options={"db_table": "inventory_operation", "ordering": ("-created_at", "-id")},
        ),
        migrations.AddIndex(
            model_name="inventoryoperation",
            index=models.Index(fields=["business", "operation_type", "status", "id"], name="inv_operation_scope_ix"),
        ),
        migrations.AddConstraint(
            model_name="inventoryoperation",
            constraint=models.CheckConstraint(condition=Q(operation_type="transfer", destination_warehouse__isnull=False) | ~Q(operation_type="transfer"), name="inv_op_transfer_dest_ck"),
        ),
        migrations.AddConstraint(
            model_name="inventoryoperation",
            constraint=models.CheckConstraint(condition=Q(operation_type="transfer") | Q(destination_warehouse__isnull=True), name="inv_op_no_dest_ck"),
        ),
        migrations.AddConstraint(
            model_name="inventoryoperation",
            constraint=models.CheckConstraint(
                condition=(
                    Q(operation_type="issue", status__in=("draft", "posted", "reversed", "cancelled"))
                    | Q(operation_type="transfer", status__in=("draft", "in_transit", "received", "cancelled"))
                    | Q(operation_type="stocktake", status__in=("draft", "approved", "cancelled"))
                ),
                name="inv_op_state_ck",
            ),
        ),
        migrations.CreateModel(
            name="InventoryOperationLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.DecimalField(decimal_places=12, max_digits=36)),
                ("unit", models.CharField(choices=[("kg", "kg"), ("g", "g"), ("l", "l"), ("ml", "ml"), ("pc", "pc"), ("pk", "pk")], max_length=2)),
                ("system_quantity", models.DecimalField(blank=True, decimal_places=12, max_digits=36, null=True)),
                ("counted_quantity", models.DecimalField(blank=True, decimal_places=12, max_digits=36, null=True)),
                ("counted_unit_cost", models.DecimalField(blank=True, decimal_places=48, max_digits=70, null=True)),
                ("counted_by_id", models.PositiveBigIntegerField(blank=True, null=True)),
                ("counted_at", models.DateTimeField(blank=True, null=True)),
                ("snapshot_movement_id", models.PositiveBigIntegerField(blank=True, null=True)),
                ("transfer_unit_cost", models.DecimalField(blank=True, decimal_places=48, max_digits=70, null=True)),
                ("ingredient", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="inventory.ingredient")),
                ("operation", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lines", to="inventory.inventoryoperation")),
            ],
            options={"db_table": "inventory_operation_line"},
        ),
        migrations.AddConstraint(
            model_name="inventoryoperationline",
            constraint=models.UniqueConstraint(fields=("operation", "ingredient"), name="inv_operation_item_uq"),
        ),
        migrations.AddConstraint(
            model_name="inventoryoperationline",
            constraint=models.CheckConstraint(condition=Q(quantity__gte=0), name="inv_operation_qty_nonneg_ck"),
        ),
        migrations.AddConstraint(
            model_name="inventoryoperationline",
            constraint=models.CheckConstraint(condition=Q(counted_quantity__isnull=True) | Q(counted_quantity__gte=0), name="inv_operation_count_nonneg_ck"),
        ),
        migrations.AddConstraint(
            model_name="inventoryoperationline",
            constraint=models.CheckConstraint(condition=Q(system_quantity__isnull=True) | Q(system_quantity__gte=0), name="inv_op_snapshot_ck"),
        ),
        migrations.AddConstraint(
            model_name="inventoryoperationline",
            constraint=models.CheckConstraint(condition=Q(counted_unit_cost__isnull=True) | Q(counted_unit_cost__gte=0), name="inv_op_count_cost_ck"),
        ),
        migrations.AddConstraint(
            model_name="inventoryoperationline",
            constraint=models.CheckConstraint(condition=Q(transfer_unit_cost__isnull=True) | Q(transfer_unit_cost__gte=0), name="inv_op_transfer_cost_ck"),
        ),
    ]
