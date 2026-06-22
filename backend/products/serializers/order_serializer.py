from rest_framework import serializers




class OrderItemCreateInputSerializer(serializers.Serializer):
    menu_item_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    notes = serializers.CharField(required=False, allow_null=True)

class OrderItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)

    menu_item_id = serializers.IntegerField()
    menu_item_name = serializers.CharField()

    quantity = serializers.IntegerField()
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2)

    notes = serializers.CharField(allow_null=True, required=False)


class CreateOrderInputSerializer(serializers.Serializer):
    customer_name = serializers.CharField(required=False)
    customer_phone = serializers.CharField(required=False, allow_blank=True)

    table_id = serializers.CharField(required=False, allow_null=True)

    order_type = serializers.ChoiceField(
        choices=["dine_in", "takeaway", "delivery"]
    )

    items = OrderItemCreateInputSerializer(many=True)

    notes = serializers.CharField(required=False, allow_null=True)

class OrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()

    customer_name = serializers.CharField()
    customer_phone = serializers.CharField(allow_null=True)

    order_type = serializers.CharField()
    status = serializers.CharField()

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
        choices=[
            "confirmed",
            "preparing",
            "ready",
            "completed",
            "cancelled",
        ]
    )



