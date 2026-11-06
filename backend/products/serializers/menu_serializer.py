from rest_framework import serializers

from accounts.models import Business
from products.models import MenuItem
from products.models import Menu
from inventory.models import Recipe




class BusinessRecipeField(serializers.PrimaryKeyRelatedField):
    """Resolve recipe IDs only inside the authenticated business."""

    def get_queryset(self):
        business = self.context.get("business")
        if business is None:
            return Recipe.objects.none()
        return Recipe.objects.filter(business=business, is_active=True)


class MenuItemCreateSerializer(serializers.Serializer):

    recipe_id = BusinessRecipeField(
        source="recipe",
        queryset=Recipe.objects.none(),
        required=False,
        allow_null=True,
    )

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

    image_url = serializers.CharField(
        required=False,
        allow_null=True
    )

    is_available = serializers.BooleanField(
        required=False,
        default=True
    )




class MenuItemSerializer(serializers.ModelSerializer):
    recipe_id = serializers.IntegerField(read_only=True)
    recipe_name = serializers.CharField(source="recipe.name", read_only=True, allow_null=True)

    class Meta:
        model = MenuItem
        fields = [
            "id",
            "name",
            "description",
            "price",
            "image_url",
            "is_available",
            "recipe_id",
            "recipe_name",
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
    recipe_id = BusinessRecipeField(
        source="recipe",
        queryset=Recipe.objects.none(),
        required=False,
        allow_null=True,
    )

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

    image_url = serializers.CharField(
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





class PublicMenuItemSerializer(serializers.ModelSerializer):
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


class PublicMenuSerializer(serializers.ModelSerializer):
    items = PublicMenuItemSerializer(many=True, read_only=True)

    class Meta:
        model = Menu
        fields = "__all__"

class PublicRestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = "__all__"
