# Add the StockTransaction field required by the current inventory model.
# The remaining inventory model/migration drift is intentionally deferred
# because Django's complete autodetected migration includes destructive
# legacy-model and field removals.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_recipe_recipeinput_recipeoutput_stock_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='stocktransaction',
            name='balance_after',
            field=models.DecimalField(
                decimal_places=3,
                max_digits=12,
                null=True,
            ),
        ),
    ]
