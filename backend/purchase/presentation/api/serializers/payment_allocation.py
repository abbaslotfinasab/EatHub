from rest_framework import serializers


class CreatePaymentAllocationSerializer(serializers.Serializer):
    accounts_payable_id = serializers.IntegerField(min_value=1)
    supplier_payment_id = serializers.IntegerField(min_value=1)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)

    def to_internal_value(self, data):
        allowed = {"accounts_payable_id", "supplier_payment_id", "amount"}
        extra = set(data) - allowed
        if extra:
            raise serializers.ValidationError({
                field: "This field is not allowed."
                for field in sorted(extra)
            })
        return super().to_internal_value(data)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value


class PaymentAllocationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    business_id = serializers.IntegerField()
    accounts_payable_id = serializers.IntegerField()
    supplier_payment_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    allocated_at = serializers.DateTimeField()
    created_at = serializers.DateTimeField(allow_null=True)
    updated_at = serializers.DateTimeField(allow_null=True)
