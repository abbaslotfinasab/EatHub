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
        return Recipe.objects.filter(business=business)


class MenuItemCreateSerializer(serializers.Serializer):

    product_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)

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
    product_id = serializers.IntegerField(read_only=True, allow_null=True)
    product_name = serializers.CharField(source="product.name", read_only=True, allow_null=True)
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
            "product_id",
            "product_name",
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
    product_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)

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

    def validate_items(self, items):
        menu = self.instance
        if menu is None:
            return items

        item_ids = [item["id"] for item in items if "id" in item]
        if len(item_ids) != len(set(item_ids)):
            raise serializers.ValidationError("A menu item may only appear once.")

        existing_ids = set(
            MenuItem.objects.filter(
                menu=menu,
                business=menu.business,
                id__in=item_ids,
            ).values_list("id", flat=True)
        )
        unknown_ids = set(item_ids) - existing_ids
        if unknown_ids:
            raise serializers.ValidationError(
                "One or more menu item IDs do not belong to this menu."
            )

        for item in items:
            if "id" not in item and ("name" not in item or "price" not in item):
                raise serializers.ValidationError(
                    "New menu items require both name and price."
                )
        return items





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
