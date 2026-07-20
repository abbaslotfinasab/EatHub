from rest_framework import serializers

from products.models import Customer, Order


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

    menu_item_id = serializers.IntegerField()
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

    notes = serializers.CharField(required=False, allow_null=True)


class OrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()

    customer_id = serializers.IntegerField(source="customer.id", read_only=True)

    table = serializers.IntegerField(required=False,
                                     allow_null=True, )

    customer_name = serializers.CharField(source="customer.name", read_only=True)
    customer_phone = serializers.CharField(source="customer.phone", read_only=True)

    order_type = serializers.CharField()
    status = serializers.CharField()

    payment_method = serializers.CharField()

    payment_status = serializers.CharField()

    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    discount = serializers.DecimalField(max_digits=12, decimal_places=2)
    tax = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    notes = serializers.CharField(allow_null=True)

    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    items = OrderItemSerializer(many=True)


class OrderStatusUpdateSerializer(serializers.Serializer):

    status = serializers.ChoiceField(
        choices=Order.Status.choices,
    )

    payment_status = serializers.ChoiceField(
        choices=Order.PaymentStatus.choices,
        required=False,
    )

    payment_method = serializers.ChoiceField(
        choices=Order.PaymentMethod.choices,
        required=False,
    )


class UpdateOrderInputSerializer(serializers.Serializer):
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        required=False,
        allow_null=True,
    )

    table_id = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    order_type = serializers.ChoiceField(
        choices=["dine_in", "takeaway", "delivery"],
        required=False,
    )

    items = OrderItemCreateInputSerializer(
        many=True,
        required=False
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
