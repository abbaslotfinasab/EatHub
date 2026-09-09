from decimal import Decimal

from rest_framework import serializers


class CreateGoodsReceiptItemSerializer(serializers.Serializer):
    purchase_order_item_id = serializers.IntegerField(min_value=1)
    received_quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=Decimal("0"),
    )
    rejected_quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=Decimal("0"),
        required=False,
        default=Decimal("0"),
    )


class CreateGoodsReceiptSerializer(serializers.Serializer):
    purchase_order_id = serializers.IntegerField(min_value=1)
    received_date = serializers.DateTimeField()
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    items = CreateGoodsReceiptItemSerializer(many=True, allow_empty=False)


class GoodsReceiptItemSerializer(serializers.Serializer):
    purchase_order_item_id = serializers.IntegerField()
    received_quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
    )
    rejected_quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
    )


class GoodsReceiptSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    business_id = serializers.IntegerField()
    purchase_order_id = serializers.IntegerField()
    received_by_id = serializers.IntegerField()
    received_date = serializers.DateTimeField()
    notes = serializers.CharField()
    items = GoodsReceiptItemSerializer(many=True)
    created_at = serializers.DateTimeField(allow_null=True)
    updated_at = serializers.DateTimeField(allow_null=True)
