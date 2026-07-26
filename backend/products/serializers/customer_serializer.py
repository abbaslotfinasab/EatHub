from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from products.models import Customer, CustomerAccount, CustomerTransaction


class CreateCustomerSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    phone = serializers.CharField(max_length=20)


class UpdateCustomerSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120, required=False)
    phone = serializers.CharField(max_length=20, required=False)


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "phone",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


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
            "description",
            "created_at",
        ]


class CustomerDetailSerializer(serializers.Serializer):
    customer = CustomerSerializer(
        read_only=True,
    )

    account = CustomerAccountSerializer(
        read_only=True,
    )

    transactions = CustomerTransactionSerializer(
        many=True,
        read_only=True,
    )

    def to_representation(self, instance):

        try:
            account = instance.account
        except ObjectDoesNotExist:
            account = None

        return {
            "customer": CustomerSerializer(instance).data,
            "account": (
                CustomerAccountSerializer(account).data
                if account else None
            ),
            "transactions": (
                CustomerTransactionSerializer(
                    account.transactions.all(),
                    many=True,
                ).data
                if account else []
            ),
        }


class CustomerBalanceSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )


class CustomerListSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(
        source="account.balance",
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True,
    )

    totalOrders = serializers.IntegerField(
        source="total_orders",
        read_only=True,
    )

    totalSpent = serializers.DecimalField(
        source="total_spent",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = Customer

        fields = [
            "id",
            "name",
            "phone",
            "balance",
            "totalOrders",
            "totalSpent",
            "created_at",
        ]
