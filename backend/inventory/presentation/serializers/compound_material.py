from rest_framework import serializers

from inventory.models import Ingredient
from inventory.presentation.serializers.master_data import StrictSerializer


class CompoundMaterialComponentWriteSerializer(StrictSerializer):
    ingredient_id = serializers.IntegerField(min_value=1)
    quantity = serializers.DecimalField(max_digits=36, decimal_places=12, min_value=0)
    unit = serializers.ChoiceField(choices=Ingredient.Unit.choices)

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Component quantity must be positive.")
        return value


class CompoundMaterialListQuerySerializer(StrictSerializer):
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, required=False, default=20)
    search = serializers.CharField(max_length=200, required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)


class CompoundMaterialCreateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=120, allow_blank=False, trim_whitespace=True)
    sku = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    unit = serializers.ChoiceField(choices=Ingredient.Unit.choices)
    is_active = serializers.BooleanField(required=False, default=True)
    components = CompoundMaterialComponentWriteSerializer(
        many=True, allow_empty=False, min_length=2, max_length=100,
    )

    def validate_sku(self, value):
        return value.strip() or None if value is not None else None

    def validate_components(self, value):
        ids = [line["ingredient_id"] for line in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("Each raw ingredient may appear only once.")
        return value


class CompoundMaterialUpdateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=120, allow_blank=False, trim_whitespace=True, required=False)
    sku = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    unit = serializers.ChoiceField(choices=Ingredient.Unit.choices, required=False)
    is_active = serializers.BooleanField(required=False)
    components = CompoundMaterialComponentWriteSerializer(
        many=True, required=False, allow_empty=False, min_length=2, max_length=100,
    )

    def validate_sku(self, value):
        return value.strip() or None if value is not None else None

    def validate_components(self, value):
        ids = [line["ingredient_id"] for line in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("Each raw ingredient may appear only once.")
        return value


class CompoundMaterialComponentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    ingredient_id = serializers.IntegerField()
    ingredient_name = serializers.CharField()
    material_type = serializers.ChoiceField(choices=("raw",))
    quantity = serializers.DecimalField(max_digits=36, decimal_places=12)
    unit = serializers.CharField()


class CompoundMaterialSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    sku = serializers.CharField(allow_null=True, allow_blank=True)
    unit = serializers.CharField()
    material_type = serializers.ChoiceField(choices=("compound",))
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    components = CompoundMaterialComponentSerializer(many=True)


class CompoundMaterialPageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    results = CompoundMaterialSerializer(many=True)
