from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0014_order_lifecycle_permissions"),
    ]

    operations = [
        migrations.AddField(
            model_name="business",
            name="inventory_enabled",
            field=models.BooleanField(default=True),
        ),
    ]
