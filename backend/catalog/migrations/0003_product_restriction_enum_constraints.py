from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0002_product_restrictions"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="productallergen",
            constraint=models.CheckConstraint(
                condition=models.Q(code__in=("celery", "cereals_gluten", "crustaceans", "eggs", "fish", "lupin", "milk", "molluscs", "mustard", "peanuts", "sesame", "soybeans", "sulphites", "tree_nuts")),
                name="cat_prod_allergen_code_ck",
            ),
        ),
        migrations.AddConstraint(
            model_name="productallergen",
            constraint=models.CheckConstraint(
                condition=models.Q(presence__in=("contains", "may_contain")),
                name="cat_prod_allergen_presence_ck",
            ),
        ),
        migrations.AddConstraint(
            model_name="productdietarytag",
            constraint=models.CheckConstraint(
                condition=models.Q(code__in=("vegan", "vegetarian", "gluten_free", "dairy_free", "halal", "kosher")),
                name="cat_prod_dietary_code_ck",
            ),
        ),
    ]
