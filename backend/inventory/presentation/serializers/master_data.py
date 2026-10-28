from rest_framework import serializers

from inventory.models import Ingredient, Warehouse


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if hasattr(data, "keys"):
            unknown = set(data.keys()) - set(self.fields.keys())
            if unknown:
                raise serializers.ValidationError(
                    {key: "Unknown or unsupported field." for key in sorted(unknown)}
                )
        return super().to_internal_value(data)


class ItemQuerySerializer(StrictSerializer):
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, required=False, default=20)
    search = serializers.CharField(required=False, allow_blank=True, max_length=200)
    # QueryDict is treated as HTML input by DRF; BooleanField otherwise
    # defaults an omitted checkbox-like value to False.
    is_active = serializers.BooleanField(required=False, default=None, allow_null=True)
    unit = serializers.ChoiceField(choices=Ingredient.Unit.choices, required=False)
    preparation_level = serializers.ChoiceField(
        choices=Ingredient.PreparationLevel.choices, required=False
    )


class WarehouseQuerySerializer(StrictSerializer):
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, required=False, default=20)
    search = serializers.CharField(required=False, allow_blank=True, max_length=200)
    is_active = serializers.BooleanField(required=False, default=None, allow_null=True)
    is_default = serializers.BooleanField(required=False, default=None, allow_null=True)


class ItemCreateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=120, allow_blank=False, trim_whitespace=True)
    sku = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    unit = serializers.ChoiceField(choices=Ingredient.Unit.choices)
    preparation_level = serializers.ChoiceField(
        choices=Ingredient.PreparationLevel.choices,
        required=False,
        default=Ingredient.PreparationLevel.RAW,
    )
    is_active = serializers.BooleanField(required=False, default=True)

    def validate_sku(self, value):
        return value.strip() or None if value is not None else None


class ItemUpdateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=120, allow_blank=False, trim_whitespace=True, required=False)
    sku = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    unit = serializers.ChoiceField(choices=Ingredient.Unit.choices, required=False)
    preparation_level = serializers.ChoiceField(
        choices=Ingredient.PreparationLevel.choices, required=False
    )
    is_active = serializers.BooleanField(required=False)

    def validate_sku(self, value):
        return value.strip() or None if value is not None else None


class WarehouseCreateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=120, allow_blank=False, trim_whitespace=True)
    code = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(required=False, default=True)
    is_default = serializers.BooleanField(required=False, default=False)

    def validate_code(self, value):
        return value.strip() or None if value is not None else None

    def validate(self, attrs):
        if attrs.get("is_default", False) and not attrs.get("is_active", True):
            raise serializers.ValidationError({"is_default": "An inactive warehouse cannot be the default."})
        return attrs


class WarehouseUpdateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=120, allow_blank=False, trim_whitespace=True, required=False)
    code = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(required=False)
    is_default = serializers.BooleanField(required=False)

    def validate_code(self, value):
        return value.strip() or None if value is not None else None

    def validate(self, attrs):
        instance = self.instance
        active = attrs.get("is_active", instance.is_active if instance else True)
        if attrs.get("is_default") is True and not active:
            raise serializers.ValidationError({"is_default": "An inactive warehouse cannot be the default."})
        return attrs


class ItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    sku = serializers.CharField(allow_null=True, allow_blank=True)
    unit = serializers.CharField()
    preparation_level = serializers.CharField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class WarehouseSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    code = serializers.CharField(allow_null=True, allow_blank=True)
    is_active = serializers.BooleanField()
    is_default = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
