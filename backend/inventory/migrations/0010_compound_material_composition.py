from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


def prevent_lossy_reverse(apps, schema_editor):
    Component = apps.get_model("inventory", "CompoundMaterialComponent")
    if Component.objects.using(schema_editor.connection.alias).exists():
        raise RuntimeError(
            "Compound material components exist. Export or remove composition records "
            "before reversing this migration."
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0012_inventory_compound_permission"),
        ("inventory", "0009_opening_stock_entry"),
    ]

    operations = [
        migrations.CreateModel(
            name="CompoundMaterialComponent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("quantity", models.DecimalField(decimal_places=12, max_digits=36)),
                ("unit", models.CharField(choices=[("kg", "Kilogram"), ("g", "Gram"), ("l", "Liter"), ("ml", "Milliliter"), ("pc", "Piece"), ("pk", "Pack")], max_length=2)),
                ("compound", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="compound_components", to="inventory.ingredient")),
                ("ingredient", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="used_in_compound_materials", to="inventory.ingredient")),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.RunPython(migrations.RunPython.noop, prevent_lossy_reverse),
        migrations.AddConstraint(
            model_name="compoundmaterialcomponent",
            constraint=models.UniqueConstraint(fields=("compound", "ingredient"), name="inv_compound_component_uq"),
        ),
        migrations.AddConstraint(
            model_name="compoundmaterialcomponent",
            constraint=models.CheckConstraint(condition=Q(quantity__gt=0) & Q(quantity__lte=Decimal("999999999999999999999999.999999999999")), name="inv_compound_component_qty_ck"),
        ),
        migrations.AddConstraint(
            model_name="compoundmaterialcomponent",
            constraint=models.CheckConstraint(condition=~Q(compound=models.F("ingredient")), name="inv_compound_not_self_ck"),
        ),
    ]
