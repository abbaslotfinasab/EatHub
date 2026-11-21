from rest_framework import serializers

from financial.serializers import (
    CustomerAccountSerializer,
    CustomerTransactionSerializer,
)


class CreateCustomerSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    phone = serializers.CharField(max_length=20)


class UpdateCustomerSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120, required=False)
    phone = serializers.CharField(max_length=20, required=False)


class CustomerReadSerializer(serializers.Serializer):
    """Stable Customer response fields without a Django model dependency."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    phone = serializers.CharField(read_only=True)
    balance = serializers.DecimalField(
        source="account.balance",
        max_digits=12,
        decimal_places=2,
        read_only=True,
        allow_null=True,
    )
    totalOrders = serializers.IntegerField(source="total_orders", read_only=True)
    totalSpent = serializers.DecimalField(
        source="total_spent",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    created_at = serializers.DateTimeField(read_only=True)


class CustomerDetailReadSerializer(serializers.Serializer):
    """Stable Customer API envelope composed by the infrastructure read query."""

    def to_representation(self, instance):
        customer = instance["customer"]
        account = instance["account"]
        transactions = instance["transactions"]
        return {
            "customer": CustomerReadSerializer(customer).data,
            "account": CustomerAccountSerializer(account).data if account else None,
            "transactions": (
                CustomerTransactionSerializer(transactions, many=True).data
                if account
                else []
            ),
        }
