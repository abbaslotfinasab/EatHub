from rest_framework import serializers

from accounts.models import Business
from products.models import MenuItem
from products.models import Menu




class CreateMenuItemSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True
    )
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    image_url = serializers.URLField(
        required=False,
        allow_null=True
    )


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")





class MenuSerializer(serializers.ModelSerializer):

    items = MenuItemSerializer(many=True, read_only=True)

    class Meta:
        model = Menu
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")




class CreateMenuWithItemsSerializer(serializers.Serializer):

    name = serializers.CharField()
    category = serializers.CharField(
        required=False,
        allow_null=True
    )
    description = serializers.CharField(
        required=False,
        allow_null=True
    )
    sort_order = serializers.IntegerField(required=False,
        allow_null=True)
    is_active = serializers.BooleanField(
        required=False,
        allow_null=True)

    items = CreateMenuItemSerializer(many=True)


class PublicMenuSerializer(serializers.ModelSerializer):
    items = MenuItemSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Menu
        fields = (
            "id",
            "name",
            "sort_order",
            "items",
        )

class PublicRestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = "__all__"
