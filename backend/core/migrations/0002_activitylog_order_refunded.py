from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="activitylog",
            name="action",
            field=models.CharField(
                choices=[
                    ("create", "Create"),
                    ("update", "Update"),
                    ("delete", "Delete"),
                    ("order_created", "Order Created"),
                    ("order_completed", "Order Completed"),
                    ("order_cancelled", "Order Cancelled"),
                    ("order_refunded", "Order Refunded"),
                    ("stock_low", "Stock Low"),
                    ("login", "Login"),
                ],
                max_length=50,
            ),
        ),
    ]
