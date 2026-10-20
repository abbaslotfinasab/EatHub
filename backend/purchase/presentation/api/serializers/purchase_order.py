from decimal import Decimal

from rest_framework import serializers

from purchase.domain.enums.purchase_unit import PurchaseUnit


class PurchaseOrderItemWriteSerializer(serializers.Serializer):
    ingredient_id = serializers.IntegerField(min_value=1)
    quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=Decimal("0.001"),
    )
    unit_price = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("0"),
    )
    purchase_unit = serializers.ChoiceField(choices=[unit.value for unit in PurchaseUnit])


class PurchaseOrderCreateSerializer(serializers.Serializer):
    supplier_id = serializers.IntegerField(min_value=1)
    requisition_id = serializers.IntegerField(min_value=1, required=False)
    order_date = serializers.DateField()
    expected_date = serializers.DateField(required=False, allow_null=True)
    discount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("0"),
        required=False,
        default=Decimal("0"),
    )
    tax = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("0"),
        required=False,
        default=Decimal("0"),
    )
    items = PurchaseOrderItemWriteSerializer(many=True)


class PurchaseOrderUpdateSerializer(serializers.Serializer):
    items = PurchaseOrderItemWriteSerializer(many=True)
    discount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("0"),
        required=False,
        default=Decimal("0"),
    )
    tax = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("0"),
        required=False,
        default=Decimal("0"),
    )


class PurchaseOrderItemSerializer(serializers.Serializer):
    ingredient_id = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    unit_price = serializers.DecimalField(max_digits=14, decimal_places=2)
    purchase_unit = serializers.CharField(allow_null=True)


class PurchaseOrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    business_id = serializers.IntegerField()
    supplier_id = serializers.IntegerField()
    requisition_id = serializers.IntegerField(allow_null=True)
    status = serializers.CharField()
    order_date = serializers.DateField()
    expected_date = serializers.DateField(allow_null=True)
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2)
    discount = serializers.DecimalField(max_digits=14, decimal_places=2)
    tax = serializers.DecimalField(max_digits=14, decimal_places=2)
    total = serializers.DecimalField(max_digits=14, decimal_places=2)
    items = PurchaseOrderItemSerializer(many=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
