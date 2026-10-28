from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


def prevent_lossy_reverse(apps, schema_editor):
    Reservation = apps.get_model("inventory", "InventoryReservation")
    if Reservation.objects.using(schema_editor.connection.alias).exists():
        raise RuntimeError(
            "Inventory reservations exist. Export or otherwise preserve reservation "
            "history before reversing this migration."
        )


class Migration(migrations.Migration):
    dependencies = [("inventory", "0011_reconcile_inventory_model_state")]

    operations = [
        migrations.CreateModel(
            name="InventoryReservation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_type", models.CharField(max_length=64)),
                ("source_id", models.PositiveBigIntegerField(blank=True, null=True)),
                ("reason", models.TextField()),
                ("status", models.CharField(choices=[("active", "Active"), ("released", "Released")], default="active", max_length=16)),
                ("idempotency_key", models.UUIDField()),
                ("payload_fingerprint", models.CharField(max_length=64)),
                ("created_by_id", models.PositiveBigIntegerField()),
                ("released_by_id", models.PositiveBigIntegerField(blank=True, null=True)),
                ("released_at", models.DateTimeField(blank=True, null=True)),
                ("release_idempotency_key", models.UUIDField(blank=True, null=True)),
                ("release_reason", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("business", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="inventory_reservations", to="accounts.business")),
                ("warehouse", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="inventory_reservations", to="inventory.warehouse")),
            ],
            options={"db_table": "inventory_reservation", "ordering": ("-created_at", "-id")},
        ),
        migrations.AddIndex(
            model_name="inventoryreservation",
            index=models.Index(fields=["business", "status", "id"], name="inv_res_scope_status_ix"),
        ),
        migrations.AddConstraint(
            model_name="inventoryreservation",
            constraint=models.UniqueConstraint(fields=("business", "idempotency_key"), name="inv_res_create_key_uq"),
        ),
        migrations.AddConstraint(
            model_name="inventoryreservation",
            constraint=models.UniqueConstraint(fields=("business", "release_idempotency_key"), condition=Q(release_idempotency_key__isnull=False), name="inv_res_release_key_uq"),
        ),
        migrations.AddConstraint(
            model_name="inventoryreservation",
            constraint=models.UniqueConstraint(fields=("business", "source_type", "source_id"), condition=Q(status="active", source_id__isnull=False), name="inv_res_active_source_uq"),
        ),
        migrations.AddConstraint(
            model_name="inventoryreservation",
            constraint=models.CheckConstraint(condition=Q(source_type__gt=""), name="inv_res_source_type_ck"),
        ),
        migrations.AddConstraint(
            model_name="inventoryreservation",
            constraint=models.CheckConstraint(condition=Q(reason__gt=""), name="inv_res_reason_ck"),
        ),
        migrations.AddConstraint(
            model_name="inventoryreservation",
            constraint=models.CheckConstraint(condition=Q(source_id__isnull=True) | Q(source_id__gt=0), name="inv_res_source_id_ck"),
        ),
        migrations.AddConstraint(
            model_name="inventoryreservation",
            constraint=models.CheckConstraint(condition=Q(created_by_id__gt=0), name="inv_res_created_actor_ck"),
        ),
        migrations.AddConstraint(
            model_name="inventoryreservation",
            constraint=models.CheckConstraint(
                condition=(
                    Q(status="active", released_by_id__isnull=True, released_at__isnull=True,
                      release_idempotency_key__isnull=True, release_reason="")
                    | Q(status="released", released_by_id__gt=0, released_at__isnull=False,
                        release_idempotency_key__isnull=False, release_reason__gt="")
                ),
                name="inv_res_release_state_ck",
            ),
        ),
        migrations.CreateModel(
            name="InventoryReservationLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_line_id", models.PositiveBigIntegerField(blank=True, null=True)),
                ("quantity", models.DecimalField(decimal_places=12, max_digits=36)),
                ("unit", models.CharField(choices=[("kg", "kg"), ("g", "g"), ("l", "l"), ("ml", "ml"), ("pc", "pc"), ("pk", "pk")], max_length=2)),
                ("ingredient", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="inventory_reservation_lines", to="inventory.ingredient")),
                ("reservation", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lines", to="inventory.inventoryreservation")),
            ],
            options={"db_table": "inventory_reservation_line"},
        ),
        migrations.AddConstraint(
            model_name="inventoryreservationline",
            constraint=models.UniqueConstraint(fields=("reservation", "source_line_id"), condition=Q(source_line_id__isnull=False), name="inv_res_line_source_uq"),
        ),
        migrations.AddConstraint(
            model_name="inventoryreservationline",
            constraint=models.UniqueConstraint(fields=("reservation", "ingredient"), condition=Q(source_line_id__isnull=True), name="inv_res_line_item_uq"),
        ),
        migrations.AddConstraint(
            model_name="inventoryreservationline",
            constraint=models.CheckConstraint(condition=Q(source_line_id__isnull=True) | Q(source_line_id__gt=0), name="inv_res_line_source_id_ck"),
        ),
        migrations.AddConstraint(
            model_name="inventoryreservationline",
            constraint=models.CheckConstraint(
                condition=Q(quantity__gt=0) & Q(quantity__lte=Decimal("999999999999999999999999.999999999999")),
                name="inv_res_line_qty_ck",
            ),
        ),
        migrations.AddConstraint(
            model_name="inventoryreservationline",
            constraint=models.CheckConstraint(condition=Q(unit__in=("kg", "g", "l", "ml", "pc", "pk")), name="inv_res_line_unit_ck"),
        ),
        # Guard runs before the reverse operation drops either table.
        migrations.RunPython(migrations.RunPython.noop, prevent_lossy_reverse),
    ]
