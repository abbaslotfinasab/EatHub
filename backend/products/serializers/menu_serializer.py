from rest_framework import serializers

from accounts.models import Business
from products.models import MenuItem
from products.models import Menu




class MenuItemCreateSerializer(serializers.Serializer):

    product_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)

    recipe_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)

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
    product_name = serializers.SerializerMethodField()
    recipe_id = serializers.IntegerField(read_only=True)
    recipe_name = serializers.SerializerMethodField()
    recipe_allergens = serializers.SerializerMethodField()
    catalog_product_allergens = serializers.SerializerMethodField()

    def _recipe_read_model(self, obj):
        if obj.recipe_id is None:
            return None
        cache = getattr(self, "_recipe_read_models", {})
        key = (obj.business_id, obj.recipe_id)
        if key not in cache:
            from composition.recipe_queries import RecipeUnavailable, get_recipe_for_business
            try:
                cache[key] = get_recipe_for_business(
                    business_id=obj.business_id,
                    recipe_id=obj.recipe_id,
                )
            except RecipeUnavailable:
                cache[key] = None
            self._recipe_read_models = cache
        return cache[key]

    def _product_read_model(self, obj):
        if obj.product_id is None:
            return None
        cache = getattr(self, "_product_read_models", {})
        key = (obj.business_id, obj.product_id)
        if key not in cache:
            from catalog.application.services import ProductCatalogService, ProductNotFound
            try:
                cache[key] = ProductCatalogService.get_product_read_model_for_business(
                    business_id=obj.business_id,
                    product_id=obj.product_id,
                )
            except ProductNotFound:
                cache[key] = None
            self._product_read_models = cache
        return cache[key]

    def get_product_name(self, obj):
        product = self._product_read_model(obj)
        return None if product is None else product["name"]

    def get_recipe_name(self, obj):
        recipe = self._recipe_read_model(obj)
        return None if recipe is None else recipe.name

    def get_recipe_allergens(self, obj):
        recipe = self._recipe_read_model(obj)
        return None if recipe is None else list(recipe.allergens)

    def get_catalog_product_allergens(self, obj):
        product = self._product_read_model(obj)
        return None if product is None else list(product["allergens"])

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
            "recipe_allergens",
            "catalog_product_allergens",
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

    recipe_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)

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
