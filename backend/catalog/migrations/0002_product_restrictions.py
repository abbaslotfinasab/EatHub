import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductAllergen",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.CharField(choices=[("celery", "Celery"), ("cereals_gluten", "Cereals containing gluten"), ("crustaceans", "Crustaceans"), ("eggs", "Eggs"), ("fish", "Fish"), ("lupin", "Lupin"), ("milk", "Milk"), ("molluscs", "Molluscs"), ("mustard", "Mustard"), ("peanuts", "Peanuts"), ("sesame", "Sesame"), ("soybeans", "Soybeans"), ("sulphites", "Sulphur dioxide and sulphites"), ("tree_nuts", "Tree nuts")], max_length=32)),
                ("presence", models.CharField(choices=[("contains", "Contains"), ("may_contain", "May contain")], default="contains", max_length=16)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="allergen_declarations", to="catalog.product")),
            ],
            options={"ordering": ("code",), "constraints": [models.UniqueConstraint(fields=("product", "code"), name="catalog_product_allergen_uq")]},
        ),
        migrations.CreateModel(
            name="ProductDietaryTag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.CharField(choices=[("vegan", "Vegan"), ("vegetarian", "Vegetarian"), ("gluten_free", "Gluten-free"), ("dairy_free", "Dairy-free"), ("halal", "Halal"), ("kosher", "Kosher")], max_length=24)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="dietary_tags", to="catalog.product")),
            ],
            options={"ordering": ("code",), "constraints": [models.UniqueConstraint(fields=("product", "code"), name="catalog_product_dietary_tag_uq")]},
        ),
    ]
