import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0014_register_retained_legacy_purchase_tables"),
    ]

    operations = [
        migrations.CreateModel(
            name="IngredientAllergen",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.CharField(
                    choices=[
                        ("celery", "Celery"),
                        ("cereals_gluten", "Cereals Gluten"),
                        ("crustaceans", "Crustaceans"),
                        ("eggs", "Eggs"),
                        ("fish", "Fish"),
                        ("lupin", "Lupin"),
                        ("milk", "Milk"),
                        ("molluscs", "Molluscs"),
                        ("mustard", "Mustard"),
                        ("peanuts", "Peanuts"),
                        ("sesame", "Sesame"),
                        ("soybeans", "Soybeans"),
                        ("sulphites", "Sulphites"),
                        ("tree_nuts", "Tree Nuts"),
                    ],
                    max_length=32,
                )),
                ("presence", models.CharField(
                    choices=[("contains", "Contains"), ("may_contain", "May contain")],
                    max_length=16,
                )),
                ("ingredient", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="allergen_declarations",
                    to="inventory.ingredient",
                )),
            ],
            options={"ordering": ["code"]},
        ),
        migrations.AddConstraint(
            model_name="ingredientallergen",
            constraint=models.UniqueConstraint(
                fields=("ingredient", "code"),
                name="inv_ingredient_allergen_uq",
            ),
        ),
    ]
