from decimal import Decimal

from rest_framework import serializers
from rest_framework.fields import empty


class OptionalReasonField(serializers.CharField):
    def run_validation(self, data=empty):
        if data is not empty and data is not None:
            if not isinstance(data, str):
                raise serializers.ValidationError("Expected a string.")
            if len(data) > self.max_length:
                raise serializers.ValidationError(
                    f"Ensure this field has no more than {self.max_length} characters."
                )
        return super().run_validation(data)

    def to_internal_value(self, data):
        if data is not None and not isinstance(data, str):
            raise serializers.ValidationError("Expected a string.")
        return super().to_internal_value(data)


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


class RejectRequisitionSerializer(serializers.Serializer):
    reason = OptionalReasonField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=2000,
        default=None,
    )


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


class RequisitionDecisionSerializer(serializers.Serializer):
    decision = serializers.CharField()
    actor_id = serializers.IntegerField()
    actor_name = serializers.CharField()
    decided_at = serializers.DateTimeField()
    previous_status = serializers.CharField()
    resulting_status = serializers.CharField()
    rejection_reason = serializers.CharField(allow_null=True)
