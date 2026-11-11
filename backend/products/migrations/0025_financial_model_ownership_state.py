from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("financial", "0001_model_ownership"),
        ("products", "0024_customer_model_ownership_state"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name="CustomerAccount"),
                migrations.DeleteModel(name="OrderRefund"),
                migrations.DeleteModel(name="CustomerTransaction"),
            ],
        ),
    ]
