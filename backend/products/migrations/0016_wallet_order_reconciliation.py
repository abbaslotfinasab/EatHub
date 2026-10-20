from django.db import migrations, models


def mark_existing_order_debits_as_settlements(apps, schema_editor):
    CustomerTransaction = apps.get_model("products", "CustomerTransaction")
    CustomerTransaction.objects.using(schema_editor.connection.alias).filter(
        order__isnull=False,
        type="debit",
    ).update(is_order_settlement=True)


class Migration(migrations.Migration):
    dependencies = [("products", "0015_unique_order_wallet_debit")]

    operations = [
        migrations.AddField(
            model_name="customertransaction",
            name="is_order_settlement",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(
            mark_existing_order_debits_as_settlements,
            migrations.RunPython.noop,
        ),
        migrations.RemoveConstraint(
            model_name="customertransaction",
            name="uniq_wallet_debit_per_order",
        ),
    ]
