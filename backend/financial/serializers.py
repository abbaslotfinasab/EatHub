from rest_framework import serializers


class CustomerAccountSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    customer = serializers.IntegerField(source="customer_id", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    customer_phone = serializers.CharField(source="customer.phone", read_only=True)
    balance = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class CustomerTransactionSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    account = serializers.IntegerField(source="account_id", read_only=True)
    order = serializers.IntegerField(source="order_id", read_only=True, allow_null=True)
    type = serializers.CharField(read_only=True)
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    balance_after = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    description = serializers.CharField(
        read_only=True, allow_null=True, allow_blank=True
    )
    created_at = serializers.DateTimeField(read_only=True)


class CustomerBalanceSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
