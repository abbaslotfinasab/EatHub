from rest_framework import serializers

from inventory.models import PurchaseOrder


class PurchaseOrderItemCreateInputSerializer(serializers.Serializer):

    item_type = serializers.ChoiceField(
        choices=[
            ("ingredient", "Ingredient"),
            ("menu_item", "Menu Item"),
        ]
    )

    item_id = serializers.IntegerField()

    quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
    )

    unit_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    total_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )




class CreatePurchaseOrderInputSerializer(serializers.Serializer):

    supplier_id = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    supplier_name = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    supplier_number = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    type = serializers.ChoiceField(
        choices=PurchaseOrder.Type.choices,
        default=PurchaseOrder.Type.PURCHASE,
    )

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    discount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
    )

    tax = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
    )

    invoice_number = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    items = PurchaseOrderItemCreateInputSerializer(
        many=True,
    )


class UpdatePurchaseOrderInputSerializer(serializers.Serializer):

    supplier_id = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    supplier_name = serializers.CharField(
        required=False,
    )

    supplier_number = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    type = serializers.ChoiceField(
        choices=PurchaseOrder.Type.choices,
        required=False,
    )

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    discount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
    )

    tax = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
    )

    invoice_number = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    items = PurchaseOrderItemCreateInputSerializer(
        many=True,
        required=False,
    )


class PurchaseOrderItemSerializer(serializers.Serializer):

    id = serializers.IntegerField()

    purchase_order_id = serializers.IntegerField(
        source="purchase_order.id"
    )

    item_type = serializers.ChoiceField(
        choices=[
            ("ingredient", "Ingredient"),
            ("menu_item", "Menu Item"),
        ]
    )

    item_id = serializers.IntegerField()

    quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
    )

    unit_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    total_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    created_at = serializers.DateTimeField()

    updated_at = serializers.DateTimeField()


class PurchaseOrderSerializer(serializers.Serializer):

    id = serializers.IntegerField()

    supplier_id = serializers.CharField(
        allow_null=True,
    )

    supplier_name = serializers.CharField()

    supplier_number = serializers.CharField()

    type = serializers.CharField()

    status = serializers.CharField()

    subtotal = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    discount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    tax = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    total_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    invoice_number = serializers.CharField(
        allow_null=True,
    )

    notes = serializers.CharField(
        allow_null=True,
    )

    created_at = serializers.DateTimeField()

    updated_at = serializers.DateTimeField()

    items = PurchaseOrderItemSerializer(
        many=True,
    )


class PurchaseOrderStatusUpdateSerializer(serializers.Serializer):

    status = serializers.ChoiceField(
        choices=PurchaseOrder.Status.choices,
    )