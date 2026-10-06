import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("purchase", "0005_purchaseinvoice_lifecycle"),
    ]

    operations = [
        migrations.AddField(
            model_name="purchaseinvoice",
            name="matching_status",
            field=models.CharField(
                choices=[
                    ("not_matched", "Not matched"),
                    ("pending_receipt", "Pending receipt"),
                    ("matched", "Matched"),
                    ("exception", "Exception"),
                ],
                default="not_matched",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="purchaseinvoice",
            name="matched_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="purchaseinvoiceitem",
            name="purchase_order_item",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="purchase_invoice_items",
                to="purchase.purchaseorderitem",
            ),
        ),
    ]
