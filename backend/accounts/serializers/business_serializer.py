from django.core.files.storage import default_storage
from rest_framework import serializers

from accounts.models import Business


class BusinessCreateSerializer(serializers.ModelSerializer):
    logo = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Business
        fields = ["name", "number", "address", "logo"]

    def validate_logo(self, value):
        if value in (None, ""):
            return value
        if not value.startswith(f"uploads/businesses/logos/{self.context['request'].user.pk}/") or ".." in value.split("/"):
            raise serializers.ValidationError("مسیر لوگوی کسب‌وکار معتبر نیست.")
        if not default_storage.exists(value):
            raise serializers.ValidationError("لوگوی آپلودشده پیدا نشد.")
        return value


class BusinessSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(read_only=True)

    class Meta:
        model = Business
        fields = ("id", "name", "slug", "logo", "number", "address")


class BusinessProfileUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, max_length=255)
    number = serializers.CharField(required=False, allow_blank=True, max_length=20)
    address = serializers.CharField(required=False, allow_blank=True)
    logo = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def validate_logo(self, value):
        if value in (None, ""):
            return None
        user_id = self.context["request"].user.pk
        if not value.startswith(f"uploads/businesses/logos/{user_id}/") or ".." in value.split("/"):
            raise serializers.ValidationError("مسیر لوگوی کسب‌وکار معتبر نیست.")
        if not default_storage.exists(value):
            raise serializers.ValidationError("لوگوی آپلودشده پیدا نشد.")
        return value


class BusinessInventorySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ("inventory_enabled",)
