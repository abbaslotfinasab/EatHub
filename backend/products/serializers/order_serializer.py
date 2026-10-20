from rest_framework import serializers

from accounts.serializers.business_serializer import BusinessSerializer
from products.models import Customer, Order, CustomerTransaction
from products.serializers.customer_serializer import CustomerSerializer


class OrderItemCreateInputSerializer(serializers.Serializer):
    menu_item_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )


class OrderItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)

    order_id = serializers.IntegerField(read_only=True)

    menu_item_id = serializers.IntegerField(allow_null=True)
    menu_item_name = serializers.CharField()

    quantity = serializers.IntegerField()
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2)

    notes = serializers.CharField(allow_null=True, required=False)


class CreateOrderInputSerializer(serializers.Serializer):
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        source="customer",
        required=False,
        allow_null=True,
    )
    table = serializers.IntegerField(required=False,
                                     allow_null=True,)

    order_type = serializers.ChoiceField(
        choices=["dine_in", "takeaway", "delivery"]
    )

    items = OrderItemCreateInputSerializer(many=True)

    notes = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
    )

class OrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()

    customer = CustomerSerializer(allow_null=True)

    table = serializers.IntegerField(
        required=False,
        allow_null=True,
    )

    business = BusinessSerializer(read_only=True)

    order_type = serializers.CharField()
    status = serializers.CharField()

    payment_method = serializers.CharField()
    payment_status = serializers.CharField()

    subtotal = serializers.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    discount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    tax = serializers.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    total_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    customer_balance = serializers.SerializerMethodField()

    notes = serializers.CharField(
        allow_null=True
    )

    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    items = OrderItemSerializer(many=True)

    def get_customer_balance(self, obj):
        transaction = (
            CustomerTransaction.objects
            .filter(order=obj)
            .order_by("-created_at")
            .first()
        )

        if transaction is None:
            return None

        return transaction.balance_after
class OrderStatusUpdateSerializer(serializers.Serializer):

    status = serializers.ChoiceField(
        choices=Order.Status.choices,
        required=False,
    )

    payment_status = serializers.ChoiceField(
        choices=Order.PaymentStatus.choices,
        required=False,
    )

    payment_method = serializers.ChoiceField(
        choices=Order.PaymentMethod.choices,
        required=False,
    )

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("At least one order field must be provided.")
        return attrs


class OrderRefundInputSerializer(serializers.Serializer):
    idempotency_key = serializers.UUIDField()
    reason = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
    reference = serializers.CharField(required=False, allow_blank=True, max_length=200)
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, min_value=0
    )
    confirm_external_refund = serializers.BooleanField(required=False, default=False)


class UpdateOrderInputSerializer(serializers.Serializer):
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        required=False,
        allow_null=True,
    )

    table = serializers.IntegerField(
        required=False,
        allow_null=True,
    )

    order_type = serializers.ChoiceField(
        choices=["dine_in", "takeaway", "delivery"],
        required=False,
    )

    items = OrderItemCreateInputSerializer(
        many=True,
        required=False
    )

    discount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        min_value=0,
    )

    tax = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        min_value=0,
    )

    notes = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    def validate(self, attrs):
        # جلوگیری از آپدیت خالی
        if not attrs:
            raise serializers.ValidationError(
                "At least one field must be provided."
            )
        return attrs
