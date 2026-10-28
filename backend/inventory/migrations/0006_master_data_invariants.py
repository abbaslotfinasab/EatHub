from django.db import migrations, models
from django.db.models import Count, Q


def reject_existing_conflicts(apps, schema_editor):
    """Fail closed instead of silently rewriting existing master data."""
    database = schema_editor.connection.alias
    Ingredient = apps.get_model("inventory", "Ingredient")
    Warehouse = apps.get_model("inventory", "Warehouse")

    duplicate_sku_groups = list(
        Ingredient.objects.using(database)
        .exclude(sku__isnull=True)
        .exclude(sku="")
        .values("business_id", "sku")
        .annotate(row_count=Count("id"))
        .filter(row_count__gt=1)
        .order_by("business_id", "sku")[:20]
    )
    duplicate_default_groups = list(
        Warehouse.objects.using(database)
        .filter(is_active=True, is_default=True)
        .values("business_id")
        .annotate(row_count=Count("id"))
        .filter(row_count__gt=1)
        .order_by("business_id")[:20]
    )
    duplicate_skus = [
        {
            "business_id": group["business_id"],
            "sku": group["sku"],
            "item_ids": list(
                Ingredient.objects.using(database)
                .filter(business_id=group["business_id"], sku=group["sku"])
                .order_by("id")
                .values_list("id", flat=True)
            ),
        }
        for group in duplicate_sku_groups
    ]
    duplicate_defaults = [
        {
            "business_id": group["business_id"],
            "warehouse_ids": list(
                Warehouse.objects.using(database)
                .filter(business_id=group["business_id"], is_active=True, is_default=True)
                .order_by("id")
                .values_list("id", flat=True)
            ),
        }
        for group in duplicate_default_groups
    ]
    if duplicate_skus or duplicate_defaults:
        raise RuntimeError(
            "Inventory master-data constraints were not applied because existing "
            f"conflicts need an owner-approved resolution. Duplicate SKU records "
            f"(business_id, sku, item_ids): {duplicate_skus}; duplicate active "
            f"default records (business_id, warehouse_ids): {duplicate_defaults}."
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0010_inventory_master_permissions"),
        ("inventory", "0005_retire_legacy_purchase_models_state"),
    ]

    operations = [
        migrations.RunPython(reject_existing_conflicts, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="ingredient",
            constraint=models.UniqueConstraint(
                fields=("business", "sku"),
                condition=Q(sku__isnull=False) & ~Q(sku=""),
                name="inv_item_business_sku_uq",
            ),
        ),
        migrations.AddConstraint(
            model_name="warehouse",
            constraint=models.UniqueConstraint(
                fields=("business",),
                condition=Q(is_active=True, is_default=True),
                name="inv_wh_active_default_uq",
            ),
        ),
    ]
