from decimal import Decimal, InvalidOperation

from django.db import migrations, models
from django.db.models import Q


UNIT_VALUES = ("kg", "g", "l", "ml", "pc", "pk")
MAX_QUANTITY = Decimal("999999999999999999999999.999999999999")


def validate_existing_recipe_lines(apps, schema_editor):
    database = schema_editor.connection.alias
    for model_name in ("RecipeInput", "RecipeOutput"):
        Line = apps.get_model("inventory", model_name)
        invalid = []
        for line_id, quantity, unit, recipe_business_id, ingredient_business_id in Line.objects.using(database).values_list(
            "id", "quantity", "ingredient__unit", "recipe__business_id",
            "ingredient__business_id",
        ).iterator():
            try:
                value = quantity if isinstance(quantity, Decimal) else Decimal(str(quantity))
            except (InvalidOperation, ValueError):
                invalid.append((line_id, "invalid quantity"))
                continue
            if not value.is_finite() or value <= 0:
                invalid.append((line_id, "quantity must be finite and positive"))
            elif unit not in UNIT_VALUES:
                invalid.append((line_id, "ingredient has unsupported unit"))
            elif recipe_business_id != ingredient_business_id:
                invalid.append((line_id, "recipe and ingredient belong to different businesses"))
            if len(invalid) >= 20:
                break
        if invalid:
            raise RuntimeError(
                f"Cannot migrate {model_name}; resolve these existing recipe lines first: {invalid}"
            )


def backfill_line_units(apps, schema_editor):
    database = schema_editor.connection.alias
    for model_name in ("RecipeInput", "RecipeOutput"):
        Line = apps.get_model("inventory", model_name)
        for line in Line.objects.using(database).select_related("ingredient").iterator():
            line.unit = line.ingredient.unit
            line.save(using=database, update_fields=("unit",))


class Migration(migrations.Migration):
    dependencies = [("inventory", "0007_inventory_operations")]

    operations = [
        migrations.RunPython(validate_existing_recipe_lines, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="recipeinput",
            name="quantity",
            field=models.DecimalField(max_digits=36, decimal_places=12),
        ),
        migrations.AlterField(
            model_name="recipeoutput",
            name="quantity",
            field=models.DecimalField(max_digits=36, decimal_places=12),
        ),
        migrations.AddField(
            model_name="recipeinput",
            name="unit",
            field=models.CharField(
                choices=[(value, value) for value in UNIT_VALUES],
                max_length=2,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="recipeoutput",
            name="unit",
            field=models.CharField(
                choices=[(value, value) for value in UNIT_VALUES],
                max_length=2,
                null=True,
            ),
        ),
        migrations.RunPython(backfill_line_units, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="recipeinput",
            name="unit",
            field=models.CharField(
                choices=[(value, value) for value in UNIT_VALUES], max_length=2
            ),
        ),
        migrations.AlterField(
            model_name="recipeoutput",
            name="unit",
            field=models.CharField(
                choices=[(value, value) for value in UNIT_VALUES], max_length=2
            ),
        ),
        migrations.AddConstraint(
            model_name="recipeinput",
            constraint=models.CheckConstraint(
                condition=Q(quantity__gt=0) & Q(quantity__lte=MAX_QUANTITY),
                name="recipe_input_quantity_positive_ck",
            ),
        ),
        migrations.AddConstraint(
            model_name="recipeoutput",
            constraint=models.CheckConstraint(
                condition=Q(quantity__gt=0) & Q(quantity__lte=MAX_QUANTITY),
                name="recipe_output_quantity_positive_ck",
            ),
        ),
        migrations.AddConstraint(
            model_name="recipeinput",
            constraint=models.CheckConstraint(
                condition=Q(unit__in=UNIT_VALUES), name="recipe_input_unit_supported_ck"
            ),
        ),
        migrations.AddConstraint(
            model_name="recipeoutput",
            constraint=models.CheckConstraint(
                condition=Q(unit__in=UNIT_VALUES), name="recipe_output_unit_supported_ck"
            ),
        ),
    ]
