from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0015_ingredient_allergens"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="ingredientallergen",
            constraint=models.CheckConstraint(
                condition=models.Q(code__in=[
                    "celery", "cereals_gluten", "crustaceans", "eggs", "fish",
                    "lupin", "milk", "molluscs", "mustard", "peanuts", "sesame",
                    "soybeans", "sulphites", "tree_nuts",
                ]),
                name="inv_ing_allergen_code_ck",
            ),
        ),
        migrations.AddConstraint(
            model_name="ingredientallergen",
            constraint=models.CheckConstraint(
                condition=models.Q(presence__in=["contains", "may_contain"]),
                name="inv_ing_allergen_presence_ck",
            ),
        ),
    ]
