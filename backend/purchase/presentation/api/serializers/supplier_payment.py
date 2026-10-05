from decimal import Decimal

from rest_framework import serializers

from purchase.domain.enums.payment_method import PaymentMethod


class CreateSupplierPaymentSerializer(serializers.Serializer):
    supplier_id = serializers.IntegerField(min_value=1)
    amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    payment_date = serializers.DateField()
    method = serializers.ChoiceField(choices=[method.value for method in PaymentMethod])


class SupplierPaymentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    business_id = serializers.IntegerField()
    supplier_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    payment_date = serializers.DateField()
    method = serializers.CharField()
    created_at = serializers.DateTimeField(allow_null=True)
    updated_at = serializers.DateTimeField(allow_null=True)
