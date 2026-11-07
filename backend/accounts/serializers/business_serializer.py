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


class BusinessProfileUpdateSerializer(serializers.ModelSerializer):
    logo = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Business
        fields = ("name", "number", "address", "logo")
        extra_kwargs = {
            "name": {"required": False},
            "number": {"required": False, "allow_blank": True},
            "address": {"required": False, "allow_blank": True},
        }

    def validate_logo(self, value):
        if value in (None, ""):
            return value
        if not value.startswith("uploads/businesses/logos/") or ".." in value.split("/"):
            raise serializers.ValidationError("مسیر لوگوی کسب‌وکار معتبر نیست.")
        if not default_storage.exists(value):
            raise serializers.ValidationError("لوگوی آپلودشده پیدا نشد.")
        return value

    def update(self, instance, validated_data):
        logo = validated_data.pop("logo", serializers.empty)
        old_logo = instance.logo.name if instance.logo else None
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if logo is not serializers.empty:
            instance.logo = logo or None
        instance.save()
        if logo is not serializers.empty and old_logo and old_logo != instance.logo.name:
            from core.services.UploadService import UploadService
            UploadService.delete(old_logo)
        return instance


class BusinessInventorySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ("inventory_enabled",)
