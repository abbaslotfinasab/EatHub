from rest_framework import serializers

from financial.models import CustomerAccount, CustomerTransaction


class CustomerAccountSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    customer_phone = serializers.CharField(source="customer.phone", read_only=True)

    class Meta:
        model = CustomerAccount
        fields = [
            "id",
            "customer",
            "customer_name",
            "customer_phone",
            "balance",
            "created_at",
            "updated_at",
        ]


class CustomerTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerTransaction
        fields = [
            "id",
            "account",
            "order",
            "type",
            "amount",
            "balance_after",
            "description",
            "created_at",
        ]


class CustomerBalanceSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
