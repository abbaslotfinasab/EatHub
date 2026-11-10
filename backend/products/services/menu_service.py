from django.db import transaction
from rest_framework.exceptions import ValidationError

from catalog.application.services import ProductCatalogService
from composition.recipe_queries import RecipeUnavailable, get_recipe_for_business
from products.models import Menu, MenuItem


def _resolve_products(*, business, items_data):
    product_ids = [
        item["product_id"]
        for item in items_data
        if item.get("product_id") is not None
    ]
    return ProductCatalogService.resolve_active_products(
        business=business,
        product_ids=product_ids,
    )


def _validate_recipe_ids(*, business, items_data):
    """Validate Recipe references through Inventory's public application query."""
    recipe_ids = {
        item["recipe_id"]
        for item in items_data
        if item.get("recipe_id") is not None
    }
    for recipe_id in recipe_ids:
        try:
            get_recipe_for_business(business_id=business.pk, recipe_id=recipe_id)
        except RecipeUnavailable as error:
            raise ValidationError({"recipe_id": "Selected recipe is not available in this business."}) from None
    return recipe_ids


class MenuService:

    @staticmethod
    @transaction.atomic
    def create_menu_with_items(*, business, validated_data):
        items_data = validated_data.pop("items", [])
        products = _resolve_products(business=business, items_data=items_data)
        _validate_recipe_ids(business=business, items_data=items_data)

        menu = Menu.objects.create(business=business, **validated_data)
        items = [
            MenuItem(
                business=business,
                menu=menu,
                name=item["name"],
                description=item.get("description"),
                price=item["price"],
                image_url=item.get("image_url"),
                is_available=item.get("is_available", True),
                product=products.get(item.get("product_id")),
                recipe_id=item.get("recipe_id"),
            )
            for item in items_data
        ]
        MenuItem.objects.bulk_create(items)
        return menu

    @staticmethod
    @transaction.atomic
    def update_menu(menu, data):
        items_data = data.pop("items", None)

        for field in ("name", "category", "description", "sort_order", "is_active"):
            if field in data:
                setattr(menu, field, data[field])
        menu.save()

        if items_data is None:
            return menu

        products = _resolve_products(business=menu.business, items_data=items_data)
        _validate_recipe_ids(business=menu.business, items_data=items_data)
        existing_items = {
            item.id: item
            for item in MenuItem.objects.filter(menu=menu, business=menu.business)
        }
        incoming_ids = set()

        for item_data in items_data:
            item_id = item_data.get("id")
            if item_id and item_id in existing_items:
                item = existing_items[item_id]
            else:
                item = MenuItem(menu=menu, business=menu.business)

            for field in ("name", "description", "price", "image_url", "is_available"):
                if field in item_data:
                    setattr(item, field, item_data[field])
            if "recipe_id" in item_data:
                item.recipe_id = item_data["recipe_id"]
            if "product_id" in item_data:
                item.product = products.get(item_data["product_id"])

            item.save()
            incoming_ids.add(item.id)

        MenuItem.objects.filter(menu=menu, business=menu.business).exclude(
            id__in=incoming_ids
        ).delete()
        return menu

    @staticmethod
    @transaction.atomic
    def delete_menu(menu):
        menu.delete()

    @staticmethod
    @transaction.atomic
    def create_item(*, business, menu, data):
        products = _resolve_products(business=business, items_data=[data])
        _validate_recipe_ids(business=business, items_data=[data])
        return MenuItem.objects.create(
            business=business,
            menu=menu,
            name=data["name"],
            description=data.get("description"),
            price=data["price"],
            image_url=data.get("image_url"),
            is_available=data.get("is_available", True),
            product=products.get(data.get("product_id")),
            recipe_id=data.get("recipe_id"),
        )

    @staticmethod
    @transaction.atomic
    def update_item(item, data):
        products = _resolve_products(business=item.business, items_data=[data])
        _validate_recipe_ids(business=item.business, items_data=[data])
        for field in ("name", "description", "price", "image_url", "is_available"):
            if field in data:
                setattr(item, field, data[field])
        if "recipe_id" in data:
            item.recipe_id = data["recipe_id"]
        if "product_id" in data:
            item.product = products.get(data["product_id"])
        item.save()
        return item

    @staticmethod
    @transaction.atomic
    def delete_item(item):
        item.delete()
