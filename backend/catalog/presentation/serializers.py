from rest_framework import serializers

from catalog.models import Product, ProductAllergen, ProductDietaryTag


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if hasattr(data, "keys"):
            unknown = set(data.keys()) - set(self.fields.keys())
            if unknown:
                raise serializers.ValidationError({
                    key: "Unknown or unsupported field." for key in sorted(unknown)
                })
        return super().to_internal_value(data)


class ProductQuerySerializer(StrictSerializer):
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, required=False, default=20)
    search = serializers.CharField(required=False, allow_blank=True, max_length=200)
    category = serializers.CharField(required=False, allow_blank=True, max_length=120)
    status = serializers.ChoiceField(choices=Product.Status.choices, required=False)


class ProductAllergenInputSerializer(StrictSerializer):
    code = serializers.ChoiceField(choices=ProductAllergen.Code.choices)
    presence = serializers.ChoiceField(choices=ProductAllergen.Presence.choices, required=False, default=ProductAllergen.Presence.CONTAINS)


class ProductCreateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=120, allow_blank=False, trim_whitespace=True)
    sku = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    category = serializers.CharField(max_length=120, required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    image_url = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    status = serializers.ChoiceField(choices=Product.Status.choices, required=False, default=Product.Status.DRAFT)
    allergens = ProductAllergenInputSerializer(many=True, required=False)
    dietary_tags = serializers.ListField(
        child=serializers.ChoiceField(choices=ProductDietaryTag.Code.choices),
        required=False,
        allow_empty=True,
    )

    def validate_sku(self, value):
        return value.strip() or None if value is not None else None

    def validate_category(self, value):
        return value.strip() or None if value is not None else None

    def validate_allergens(self, value):
        codes = [item["code"] for item in value]
        if len(codes) != len(set(codes)):
            raise serializers.ValidationError("Each allergen can only be declared once.")
        return value

    def validate_dietary_tags(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Dietary tags must be unique.")
        return value


class ProductUpdateSerializer(ProductCreateSerializer):
    name = serializers.CharField(max_length=120, allow_blank=False, trim_whitespace=True, required=False)
    sku = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    category = serializers.CharField(max_length=120, required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    image_url = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    status = serializers.ChoiceField(choices=Product.Status.choices, required=False)


class ProductSerializer(serializers.ModelSerializer):
    allergens = serializers.SerializerMethodField()
    dietary_tags = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id", "name", "sku", "category", "description", "image_url",
            "status", "allergens", "dietary_tags", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_allergens(self, obj):
        return [
            {"code": item.code, "presence": item.presence}
            for item in obj.allergen_declarations.all()
        ]

    def get_dietary_tags(self, obj):
        return [item.code for item in obj.dietary_tags.all()]
