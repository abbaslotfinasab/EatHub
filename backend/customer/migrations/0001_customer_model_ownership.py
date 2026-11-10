import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def move_customer_content_type(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    manager = ContentType.objects.using(schema_editor.connection.alias)
    old = manager.filter(app_label="products", model="customer").first()
    new_exists = manager.filter(app_label="customer", model="customer").exists()
    if old is None:
        return
    if new_exists:
        raise RuntimeError(
            "Both products.customer and customer.customer content types exist; "
            "reconcile permissions and generic references before migrating."
        )
    old.app_label = "customer"
    old.save(update_fields=["app_label"])


def reverse_customer_content_type_move(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    manager = ContentType.objects.using(schema_editor.connection.alias)
    current = manager.filter(app_label="customer", model="customer").first()
    old_exists = manager.filter(app_label="products", model="customer").exists()
    if current is None:
        return
    if old_exists:
        raise RuntimeError(
            "Both customer.customer and products.customer content types exist; "
            "manual reconciliation is required before reversing."
        )
    current.app_label = "products"
    current.save(update_fields=["app_label"])


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0016_multi_active_memberships"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("products", "0023_order_inventory_tracking_mode"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="Customer",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        ("name", models.CharField(max_length=120)),
                        ("phone", models.CharField(max_length=20)),
                        (
                            "business",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                to="accounts.business",
                            ),
                        ),
                        (
                            "user",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                    ],
                    options={"db_table": "products_customer"},
                ),
            ],
        ),
        migrations.RunPython(
            move_customer_content_type,
            reverse_customer_content_type_move,
        ),
    ]
