from rest_framework import serializers

from inventory.models import Ingredient, Recipe


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if hasattr(data, "keys"):
            unknown = set(data.keys()) - set(self.fields.keys())
            if unknown:
                raise serializers.ValidationError({
                    key: "Unknown or unsupported field." for key in sorted(unknown)
                })
        return super().to_internal_value(data)


class RecipeQuerySerializer(StrictSerializer):
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, required=False, default=20)
    search = serializers.CharField(max_length=200, required=False, allow_blank=True)
    type = serializers.ChoiceField(choices=Recipe.Type.choices, required=False)
    is_active = serializers.BooleanField(required=False, allow_null=True)


class RecipeLineWriteSerializer(StrictSerializer):
    ingredient_id = serializers.IntegerField(min_value=1)
    quantity = serializers.DecimalField(max_digits=36, decimal_places=12, min_value=0)
    unit = serializers.ChoiceField(choices=Ingredient.Unit.choices)
    notes = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)


class RecipeOutputWriteSerializer(RecipeLineWriteSerializer):
    is_primary = serializers.BooleanField(required=False, default=False)


class RecipeCreateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=150, allow_blank=False, trim_whitespace=True)
    code = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    type = serializers.ChoiceField(choices=Recipe.Type.choices, required=False, default=Recipe.Type.PREPARATION)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(required=False, default=True)
    inputs = RecipeLineWriteSerializer(many=True, required=False, default=list)
    outputs = RecipeOutputWriteSerializer(many=True, required=False, default=list)

    def validate_code(self, value):
        return value.strip() or None if value is not None else None


class RecipeUpdateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=150, allow_blank=False, trim_whitespace=True, required=False)
    code = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    type = serializers.ChoiceField(choices=Recipe.Type.choices, required=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(required=False)
    inputs = RecipeLineWriteSerializer(many=True, required=False)
    outputs = RecipeOutputWriteSerializer(many=True, required=False)

    def validate_code(self, value):
        return value.strip() or None if value is not None else None


class RecipeInputPatchSerializer(StrictSerializer):
    ingredient_id = serializers.IntegerField(min_value=1, required=False)
    quantity = serializers.DecimalField(max_digits=36, decimal_places=12, min_value=0, required=False)
    unit = serializers.ChoiceField(choices=Ingredient.Unit.choices, required=False)
    notes = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)


class RecipeOutputPatchSerializer(RecipeInputPatchSerializer):
    is_primary = serializers.BooleanField(required=False)


class RecipeLineSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    ingredient_id = serializers.IntegerField()
    ingredient_name = serializers.CharField()
    material_type = serializers.ChoiceField(choices=("raw", "compound"))
    quantity = serializers.DecimalField(max_digits=36, decimal_places=12)
    unit = serializers.CharField()
    notes = serializers.CharField(allow_blank=True, allow_null=True)
    is_primary = serializers.BooleanField(required=False)


class RecipeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    code = serializers.CharField(allow_blank=True, allow_null=True)
    type = serializers.CharField()
    description = serializers.CharField(allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField()
    inputs = RecipeLineSerializer(many=True)
    outputs = RecipeLineSerializer(many=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class RecipePageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    results = RecipeSerializer(many=True)
