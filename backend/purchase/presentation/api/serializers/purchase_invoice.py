from decimal import Decimal

from rest_framework import serializers


class CreatePurchaseInvoiceItemSerializer(serializers.Serializer):
    ingredient_id = serializers.IntegerField(min_value=1)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal("0.001"))
    unit_price = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0"))
    description = serializers.CharField(required=False, allow_blank=True, default="")
    discount_percent = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal("0"), default=Decimal("0"))
    tax_percent = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal("0"), default=Decimal("0"))


class CreatePurchaseInvoiceSerializer(serializers.Serializer):
    supplier_id = serializers.IntegerField(min_value=1)
    purchase_order_id = serializers.IntegerField(min_value=1)
    invoice_number = serializers.CharField(max_length=100)
    invoice_date = serializers.DateField()
    discount_percent = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal("0"), default=Decimal("0"))
    tax_percent = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal("0"), default=Decimal("0"))
    items = CreatePurchaseInvoiceItemSerializer(many=True, allow_empty=False)

    def validate(self, attrs):
        lifecycle_fields = {
            "status",
            "approved_at",
            "approved_by",
            "approved_by_id",
        }
        supplied = lifecycle_fields.intersection(self.initial_data)
        if supplied:
            raise serializers.ValidationError({
                field: "Lifecycle fields are managed by the server."
                for field in sorted(supplied)
            })
        return attrs


class UpdatePurchaseInvoiceSerializer(CreatePurchaseInvoiceSerializer):
    pass


class PurchaseInvoiceItemSerializer(serializers.Serializer):
    ingredient_id = serializers.IntegerField()
    description = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    unit_price = serializers.DecimalField(max_digits=14, decimal_places=2)
    discount_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    tax_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    tax_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    subtotal = serializers.DecimalField(source="line_subtotal", max_digits=14, decimal_places=2)
    total_price = serializers.DecimalField(max_digits=14, decimal_places=2)


class PurchaseInvoiceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    business_id = serializers.IntegerField()
    supplier_id = serializers.IntegerField()
    purchase_order_id = serializers.IntegerField()
    invoice_number = serializers.CharField()
    invoice_date = serializers.DateField()
    status = serializers.CharField()
    approved_at = serializers.DateTimeField(allow_null=True)
    approved_by_id = serializers.IntegerField(allow_null=True)
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2)
    discount_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    tax_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    tax_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_price = serializers.DecimalField(max_digits=14, decimal_places=2)
    items = PurchaseInvoiceItemSerializer(many=True)
    created_at = serializers.DateTimeField(allow_null=True)
    updated_at = serializers.DateTimeField(allow_null=True)
