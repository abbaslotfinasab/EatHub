from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def install_order_status_history_guards(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_editor.execute("""
        CREATE OR REPLACE FUNCTION prevent_order_status_history_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'Order status history is append-only'
                USING ERRCODE = '55000';
        END;
        $$;
    """)
    schema_editor.execute("""
        CREATE TRIGGER order_status_history_no_update_delete
        BEFORE UPDATE OR DELETE ON order_status_history
        FOR EACH ROW
        EXECUTE FUNCTION prevent_order_status_history_mutation();
    """)


def remove_order_status_history_guards(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_editor.execute(
        "DROP TRIGGER IF EXISTS order_status_history_no_truncate ON order_status_history;"
    )
    schema_editor.execute(
        "DROP TRIGGER IF EXISTS order_status_history_no_update_delete ON order_status_history;"
    )
    schema_editor.execute(
        "DROP FUNCTION IF EXISTS prevent_order_status_history_mutation();"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0028_order_status_history"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="orderstatushistory",
            name="order",
        ),
        migrations.AlterField(
            model_name="orderstatushistory",
            name="actor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="order_status_changes",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="orderstatushistory",
            name="business",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="order_status_history",
                to="accounts.business",
            ),
        ),
        migrations.RunPython(
            install_order_status_history_guards,
            reverse_code=remove_order_status_history_guards,
        ),
    ]
