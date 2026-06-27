from rest_framework import serializers

from accounts.models import Business
from products.models import MenuItem
from products.models import Menu




class MenuItemCreateSerializer(serializers.Serializer):

    name = serializers.CharField(
        max_length=120
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    image_url = serializers.URLField(
        required=False,
        allow_null=True
    )

    is_available = serializers.BooleanField(
        required=False,
        default=True
    )




class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = [
            "id",
            "name",
            "description",
            "price",
            "image_url",
            "is_available",
        ]
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

    items = MenuItemCreateSerializer(many=True)


class MenuItemUpdateSerializer(serializers.Serializer):
    id = serializers.IntegerField(
        required=False
    )

    name = serializers.CharField(
        max_length=120,
        required=False
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False
    )

    image_url = serializers.URLField(
        required=False,
        allow_null=True
    )

    is_available = serializers.BooleanField(
        required=False
    )


class UpdateMenuSerializer(serializers.Serializer):
    name = serializers.CharField(
        max_length=120,
        required=False
    )

    category = serializers.CharField(
        max_length=120,
        required=False
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    sort_order = serializers.IntegerField(
        required=False
    )

    is_active = serializers.BooleanField(
        required=False
    )

    items = MenuItemUpdateSerializer(
        many=True,
        required=False
    )





class PublicMenuSerializer(serializers.ModelSerializer):
    items = MenuItemSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Menu
        fields = "__all__"

class PublicRestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = "__all__"
