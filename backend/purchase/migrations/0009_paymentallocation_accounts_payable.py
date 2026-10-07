import django.db.models.deletion
from django.db import migrations, models


def map_legacy_allocations(apps, schema_editor):
    """Map only rows whose invoice, AP, payment, and supplier ownership agrees."""
    Allocation = apps.get_model("purchase", "PaymentAllocation")
    Payable = apps.get_model("purchase", "AccountsPayable")
    Invoice = apps.get_model("purchase", "PurchaseInvoice")
    Payment = apps.get_model("purchase", "SupplierPayment")
    Supplier = apps.get_model("purchase", "Supplier")
    database = schema_editor.connection.alias

    # Validate every historical row before writing any mappings. The migration
    # is atomic on supported production databases, and this two-pass structure
    # also avoids partial mapping on a backend without transactional DDL/data.
    mappings = []
    allocations = Allocation.objects.using(database).all().iterator()
    for allocation in allocations:
        if allocation.amount <= 0:
            raise RuntimeError(
                "Cannot migrate legacy PaymentAllocation with a nonpositive amount; "
                "reconcile the row before applying Purchase migration 0009."
            )

        invoice = Invoice.objects.using(database).filter(pk=allocation.invoice_id).values(
            "business_id", "supplier_id",
        ).first()
        if invoice is None:
            raise RuntimeError(
                "Cannot migrate legacy PaymentAllocation: its source invoice is missing. "
                "Review and reconcile this allocation before applying Purchase migration 0009."
            )

        payment = Payment.objects.using(database).filter(pk=allocation.payment_id).values(
            "business_id", "supplier_id",
        ).first()
        if payment is None:
            raise RuntimeError(
                "Cannot migrate legacy PaymentAllocation: its supplier payment is missing. "
                "Review and reconcile this allocation before applying Purchase migration 0009."
            )

        payable = Payable.objects.using(database).filter(
            source_invoice_id=allocation.invoice_id,
        ).values("id", "business_id", "supplier_id").first()
        if payable is None:
            raise RuntimeError(
                "Cannot migrate legacy PaymentAllocation: its invoice has no AccountsPayable. "
                "Review and reconcile this allocation before applying Purchase migration 0009."
            )

        supplier_id = invoice["supplier_id"]
        supplier = Supplier.objects.using(database).filter(pk=supplier_id).values(
            "business_id",
        ).first()
        if supplier is None:
            raise RuntimeError(
                "Cannot migrate legacy PaymentAllocation: its supplier is missing. "
                "Review and reconcile this allocation before applying Purchase migration 0009."
            )

        # Equal invoice/AP/payment business and supplier IDs, plus ownership
        # of that Supplier by the same business, validates all three edges.
        ownership_is_consistent = (
            invoice["business_id"] == payable["business_id"]
            == payment["business_id"]
            and invoice["supplier_id"] == payable["supplier_id"]
            == payment["supplier_id"]
            and supplier["business_id"] == invoice["business_id"]
        )
        if not ownership_is_consistent:
            raise RuntimeError(
                "Cannot migrate legacy PaymentAllocation: invoice, payable, payment, and supplier "
                "business/supplier ownership do not match. Review and reconcile this allocation "
                "before applying Purchase migration 0009."
            )

        mappings.append((allocation.pk, payable["id"], payment["business_id"], allocation.created_at))

    for allocation_id, payable_id, business_id, created_at in mappings:
        Allocation.objects.using(database).filter(pk=allocation_id).update(
            accounts_payable_id=payable_id,
            business_id=business_id,
            allocated_at=created_at,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("purchase", "0008_purchaseinvoice_posting"),
    ]

    operations = [
        migrations.AddField(
            model_name="paymentallocation",
            name="accounts_payable",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="payment_allocations",
                to="purchase.accountspayable",
            ),
        ),
        migrations.AddField(
            model_name="paymentallocation",
            name="business",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="payment_allocations",
                to="accounts.business",
            ),
        ),
        migrations.AddField(
            model_name="paymentallocation",
            name="allocated_at",
            field=models.DateTimeField(null=True),
        ),
        migrations.RunPython(map_legacy_allocations, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="paymentallocation",
            name="accounts_payable",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="payment_allocations",
                to="purchase.accountspayable",
            ),
        ),
        migrations.AlterField(
            model_name="paymentallocation",
            name="business",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="payment_allocations",
                to="accounts.business",
            ),
        ),
        migrations.AlterField(
            model_name="paymentallocation",
            name="allocated_at",
            field=models.DateTimeField(),
        ),
        migrations.AddConstraint(
            model_name="paymentallocation",
            constraint=models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="purchase_payment_allocation_amount_positive",
            ),
        ),
    ]
