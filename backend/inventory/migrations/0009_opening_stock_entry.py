from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [("inventory", "0008_recipe_line_units_and_precision")]

    operations = [
        migrations.AlterField(
            model_name="inventoryv1stockmovement",
            name="movement_type",
            field=models.CharField(
                choices=[
                    ("receipt", "Receipt"),
                    ("issue", "Issue"),
                    ("transfer_dispatch", "Transfer_Dispatch"),
                    ("transfer_receipt", "Transfer_Receipt"),
                    ("adjustment", "Adjustment"),
                    ("reversal", "Reversal"),
                    ("opening_balance", "Opening_Balance"),
                ],
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
                    | Q(movement_type="opening_balance", direction="in")
                ),
                name="inv_v1_move_type_dir_ck",
            ),
        ),
        migrations.AddConstraint(
            model_name="inventoryv1stockmovement",
            constraint=models.CheckConstraint(
                condition=(
                    ~Q(movement_type="opening_balance")
                    | Q(actor_id__isnull=False)
                ),
                name="inv_v1_opening_actor_ck",
            ),
        ),
        migrations.AlterField(
            model_name="inventoryoperation",
            name="operation_type",
            field=models.CharField(
                choices=[
                    ("issue", "Issue"),
                    ("transfer", "Transfer"),
                    ("stocktake", "Stocktake"),
                    ("opening_stock", "Opening stock"),
                ],
                max_length=16,
            ),
        ),
        migrations.RemoveConstraint(
            model_name="inventoryoperation",
            name="inv_op_state_ck",
        ),
        migrations.AddConstraint(
            model_name="inventoryoperation",
            constraint=models.CheckConstraint(
                condition=(
                    Q(operation_type="issue", status__in=("draft", "posted", "reversed", "cancelled"))
                    | Q(operation_type="transfer", status__in=("draft", "in_transit", "received", "cancelled"))
                    | Q(operation_type="stocktake", status__in=("draft", "approved", "cancelled"))
                    | Q(operation_type="opening_stock", status__in=("posted", "cancelled"))
                ),
                name="inv_op_state_ck",
            ),
        ),
    ]
