from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from customer.models import Customer
from financial.serializers import (
    CustomerAccountSerializer,
    CustomerTransactionSerializer,
)


from customer.presentation.serializers import (
    CreateCustomerSerializer,
    UpdateCustomerSerializer,
)


class CustomerSerializer(serializers.ModelSerializer):

    balance = serializers.DecimalField(
        source="account.balance",
        max_digits=12,
        decimal_places=2,
        read_only=True,
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

        read_only_fields = [
            "id",
            "balance",
            "totalOrders",
            "totalSpent",
            "created_at",
        ]

class CustomerDetailSerializer(serializers.Serializer):

    def to_representation(self, instance):

        try:
            account = instance.account
        except ObjectDoesNotExist:
            account = None

        transactions = (
            account.transactions
            .all()
            .order_by("-created_at", "-id")
            if account
            else []
        )

        return {
            "customer": CustomerSerializer(instance).data,

            "account": (
                CustomerAccountSerializer(account).data
                if account
                else None
            ),

            "transactions": (
                CustomerTransactionSerializer(
                    transactions,
                    many=True,
                ).data
                if account
                else []
            ),
        }

