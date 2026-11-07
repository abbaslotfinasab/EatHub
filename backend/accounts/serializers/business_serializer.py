from rest_framework import serializers
from accounts.models import Business



class BusinessCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ["name", "number", "address", "logo"]




class BusinessSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(read_only=True)

    class Meta:
        model = Business
        fields = (
            "id",
            "name",
            "slug",
            "logo",
            "number",
            "address",
        )

class BusinessInventorySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ("inventory_enabled",)
