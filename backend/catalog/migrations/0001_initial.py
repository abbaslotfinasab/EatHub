import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0016_multi_active_memberships"),
    ]

    operations = [
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=120)),
                ("sku", models.CharField(blank=True, max_length=50, null=True)),
                ("category", models.CharField(blank=True, max_length=120, null=True)),
                ("description", models.TextField(blank=True, null=True)),
                ("image_url", models.CharField(blank=True, max_length=500, null=True)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("active", "Active"), ("archived", "Archived")], default="draft", max_length=20)),
                ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="catalog_products", to="accounts.business")),
            ],
            options={
                "ordering": ["name", "id"],
                "indexes": [
                    models.Index(fields=["business", "status", "name"], name="catalog_prod_scope_status_ix"),
                ],
                "constraints": [
                    models.UniqueConstraint(condition=models.Q(("sku__isnull", False), models.Q(("sku", ""), _negated=True)), fields=("business", "sku"), name="catalog_product_business_sku_uq"),
                    models.CheckConstraint(condition=models.Q(("status__in", ("draft", "active", "archived"))), name="catalog_product_status_ck"),
                ],
            },
        ),
    ]
