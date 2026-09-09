from decimal import Decimal

from rest_framework import serializers


class CreateRequisitionItemSerializer(serializers.Serializer):
    ingredient_id = serializers.IntegerField(min_value=1)
    quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=Decimal("0.001"),
    )
    note = serializers.CharField(required=False, allow_blank=True, default="")


class CreateRequisitionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")
    items = CreateRequisitionItemSerializer(many=True, allow_empty=False)


class RequisitionItemSerializer(serializers.Serializer):
    ingredient_id = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    note = serializers.CharField()


class RequisitionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    business_id = serializers.IntegerField()
    requested_by_id = serializers.IntegerField()
    status = serializers.CharField()
    reason = serializers.CharField()
    items = RequisitionItemSerializer(many=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
