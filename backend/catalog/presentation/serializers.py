from rest_framework import serializers

from catalog.models import Product


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


class ProductCreateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=120, allow_blank=False, trim_whitespace=True)
    sku = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    category = serializers.CharField(max_length=120, required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    image_url = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    status = serializers.ChoiceField(choices=Product.Status.choices, required=False, default=Product.Status.DRAFT)

    def validate_sku(self, value):
        return value.strip() or None if value is not None else None

    def validate_category(self, value):
        return value.strip() or None if value is not None else None


class ProductUpdateSerializer(ProductCreateSerializer):
    name = serializers.CharField(max_length=120, allow_blank=False, trim_whitespace=True, required=False)
    sku = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    category = serializers.CharField(max_length=120, required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    image_url = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    status = serializers.ChoiceField(choices=Product.Status.choices, required=False)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "id", "name", "sku", "category", "description", "image_url",
            "status", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
