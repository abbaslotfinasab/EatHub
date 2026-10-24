from decimal import Decimal

from rest_framework import serializers

from purchase.domain.enums.purchase_unit import PurchaseUnit


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
    purchase_unit = serializers.ChoiceField(choices=[unit.value for unit in PurchaseUnit])


class CreateGoodsReceiptSerializer(serializers.Serializer):
    idempotency_key = serializers.UUIDField(
        help_text="Client-generated UUID reused for retries of this receipt request."
    )
    purchase_order_id = serializers.IntegerField(min_value=1)
    received_date = serializers.DateTimeField()
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    warehouse_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    items = CreateGoodsReceiptItemSerializer(many=True, allow_empty=False)


class GoodsReceiptItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    purchase_order_item_id = serializers.IntegerField()
    received_quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
    )
    rejected_quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
    )
    purchase_unit = serializers.CharField(allow_null=True)


class GoodsReceiptSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    business_id = serializers.IntegerField()
    purchase_order_id = serializers.IntegerField()
    received_by_id = serializers.IntegerField()
    received_date = serializers.DateTimeField()
    notes = serializers.CharField()
    warehouse_id = serializers.IntegerField(allow_null=True)
    items = GoodsReceiptItemSerializer(many=True)
    created_at = serializers.DateTimeField(allow_null=True)
    updated_at = serializers.DateTimeField(allow_null=True)
