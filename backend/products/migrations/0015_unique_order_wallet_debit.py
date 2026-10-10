from django.db import migrations, models


def reject_existing_duplicate_order_debits(apps, schema_editor):
    transaction_model = apps.get_model("products", "CustomerTransaction")
    duplicate = (
        transaction_model.objects.using(schema_editor.connection.alias)
        .filter(type="debit", order__isnull=False)
        .values("order_id")
        .annotate(row_count=models.Count("id"))
        .filter(row_count__gt=1)
        .first()
    )
    if duplicate:
        raise RuntimeError(
            "Cannot add uniq_wallet_debit_per_order: existing duplicate order debit "
            f"found for order {duplicate['order_id']}. Review and reconcile before retrying."
        )


class Migration(migrations.Migration):
    dependencies = [("products", "0014_alter_orderitem_menu_item")]

    operations = [
        migrations.RunPython(reject_existing_duplicate_order_debits, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="customertransaction",
            constraint=models.UniqueConstraint(
                fields=("order",),
                condition=models.Q(type="debit", order__isnull=False),
                name="uniq_wallet_debit_per_order",
            ),
        ),
    ]
