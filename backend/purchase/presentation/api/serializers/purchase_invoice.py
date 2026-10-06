from decimal import Decimal

from rest_framework import serializers

from purchase.domain.enums.purchase_invoice_match_exception import PurchaseInvoiceMatchException


MATCH_EXCEPTION_MESSAGES = {
    PurchaseInvoiceMatchException.RECEIPT_PENDING: "No accepted goods receipt exists for this purchase order item.",
    PurchaseInvoiceMatchException.INVOICE_OVER_RECEIVED: "Invoice quantity exceeds the accepted quantity remaining after previous invoices.",
    PurchaseInvoiceMatchException.PRICE_VARIANCE: "Invoice unit price differs from the purchase order unit price.",
}


class PurchaseInvoiceMatchExceptionSerializer(serializers.Serializer):
    code = serializers.SerializerMethodField()
    message = serializers.SerializerMethodField()

    def get_code(self, obj):
        return obj.value

    def get_message(self, obj):
        return MATCH_EXCEPTION_MESSAGES[obj]


class PurchaseInvoiceMatchLineSerializer(serializers.Serializer):
    invoice_item_id = serializers.IntegerField()
    purchase_order_item_id = serializers.IntegerField()
    ordered_quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    accepted_received_quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    previously_invoiced_quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    current_invoice_quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    available_quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    purchase_order_unit_price = serializers.DecimalField(max_digits=14, decimal_places=2)
    invoice_unit_price = serializers.DecimalField(max_digits=14, decimal_places=2)
    price_variance = serializers.DecimalField(max_digits=14, decimal_places=2)
    exceptions = PurchaseInvoiceMatchExceptionSerializer(many=True)


class PurchaseInvoiceMatchResultSerializer(serializers.Serializer):
    invoice_id = serializers.IntegerField()
    purchase_order_id = serializers.IntegerField()
    status = serializers.CharField()
    exceptions = PurchaseInvoiceMatchExceptionSerializer(many=True)
    lines = PurchaseInvoiceMatchLineSerializer(many=True)


class LastPersistedPurchaseInvoiceMatchSerializer(serializers.Serializer):
    status = serializers.CharField()
    matched_at = serializers.DateTimeField(allow_null=True)


class PurchaseInvoiceMatchResponseSerializer(serializers.Serializer):
    current = PurchaseInvoiceMatchResultSerializer()
    last_persisted = LastPersistedPurchaseInvoiceMatchSerializer()


class CreatePurchaseInvoiceItemSerializer(serializers.Serializer):
    ingredient_id = serializers.IntegerField(min_value=1)
    purchase_order_item_id = serializers.IntegerField(min_value=1)
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
            "posted_at",
            "posted_by",
            "posted_by_id",
            "matching_status",
            "matched_at",
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
    purchase_order_item_id = serializers.IntegerField()
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
    posted_at = serializers.DateTimeField(allow_null=True)
    posted_by_id = serializers.IntegerField(allow_null=True)
    matching_status = serializers.CharField()
    matched_at = serializers.DateTimeField(allow_null=True)
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2)
    discount_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    tax_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    tax_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_price = serializers.DecimalField(max_digits=14, decimal_places=2)
    items = PurchaseInvoiceItemSerializer(many=True)
    created_at = serializers.DateTimeField(allow_null=True)
    updated_at = serializers.DateTimeField(allow_null=True)
