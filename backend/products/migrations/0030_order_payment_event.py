from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def install_order_payment_event_guards(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute("""
        CREATE OR REPLACE FUNCTION prevent_order_payment_event_mutation()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'Order payment events are append-only'
                USING ERRCODE = '55000';
        END;
        $$;
    """)
    schema_editor.execute("""
        CREATE TRIGGER order_payment_event_no_update_delete
        BEFORE UPDATE OR DELETE ON order_payment_event
        FOR EACH ROW EXECUTE FUNCTION prevent_order_payment_event_mutation();
    """)


def remove_order_payment_event_guards(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(
        "DROP TRIGGER IF EXISTS order_payment_event_no_update_delete ON order_payment_event;"
    )
    schema_editor.execute(
        "DROP FUNCTION IF EXISTS prevent_order_payment_event_mutation();"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0029_order_status_history_retention"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0017_default_order_view_permission"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrderPaymentEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order_id_snapshot", models.PositiveBigIntegerField()),
                ("event_type", models.CharField(choices=[
                    ("payment_updated", "Payment updated"),
                    ("payment_settled", "Payment settled"),
                    ("payment_refunded", "Payment refunded"),
                    ("order_total_changed", "Order total changed"),
                ], max_length=32)),
                ("from_payment_status", models.CharField(blank=True, max_length=20, null=True)),
                ("to_payment_status", models.CharField(blank=True, max_length=20, null=True)),
                ("from_payment_method", models.CharField(blank=True, max_length=30, null=True)),
                ("to_payment_method", models.CharField(blank=True, max_length=30, null=True)),
                ("from_total_amount", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("to_total_amount", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="order_payment_events", to=settings.AUTH_USER_MODEL)),
                ("business", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_payment_events", to="accounts.business")),
            ],
            options={"db_table": "order_payment_event", "ordering": ("created_at", "pk")},
        ),
        migrations.AddIndex(
            model_name="orderpaymentevent",
            index=models.Index(fields=["business", "order_id_snapshot", "created_at"], name="order_payment_evt_scope_ix"),
        ),
        migrations.RunPython(install_order_payment_event_guards, reverse_code=remove_order_payment_event_guards),
    ]
