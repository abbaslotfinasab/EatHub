from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("purchase", "0003_alter_goodsreceipt_received_date"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="purchaseinvoice",
            constraint=models.UniqueConstraint(
                fields=("business", "invoice_number"),
                name="unique_purchase_invoice_number_per_business",
            ),
        ),
    ]
