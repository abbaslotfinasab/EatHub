import django.conf
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("purchase", "0019_supplier_payment_idempotency"),
        migrations.swappable_dependency(django.conf.settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PurchaseInvoiceEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(
                    choices=[
                        ("created", "Created"),
                        ("updated", "Updated"),
                        ("approved", "Approved"),
                        ("match_persisted", "Match persisted"),
                        ("posted", "Posted"),
                        ("cancelled", "Cancelled"),
                    ],
                    max_length=30,
                )),
                ("previous_status", models.CharField(blank=True, max_length=20, null=True)),
                ("resulting_status", models.CharField(blank=True, max_length=20, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="purchase_invoice_events",
                    to=django.conf.settings.AUTH_USER_MODEL,
                )),
                ("business", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="purchase_invoice_events",
                    to="accounts.business",
                )),
                ("purchase_invoice", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="events",
                    to="purchase.purchaseinvoice",
                )),
            ],
            options={
                "ordering": ["occurred_at", "id"],
                "indexes": [
                    models.Index(
                        fields=["business", "purchase_invoice", "occurred_at"],
                        name="pur_inv_evt_biz_inv_ts_idx",
                    ),
                ],
            },
        ),
    ]
