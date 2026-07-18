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


class CustomerDetailSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        source="account.balance",
        read_only=True
    )

    total_orders = serializers.IntegerField(
        read_only=True
    )

    total_spent = serializers.DecimalField(
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
            "created_at",
        ]


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


class CreditAccountSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    description = serializers.CharField(required=False, allow_null=True)


class DebitAccountSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    description = serializers.CharField(required=False, allow_null=True)



class AdjustAccountSerializer(serializers.Serializer):

    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
    )