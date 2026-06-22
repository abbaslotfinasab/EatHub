from django.db import transaction
from products.models import Menu, MenuItem


class MenuService:

    @staticmethod
    @transaction.atomic
    def create_menu_with_items(*, business, validated_data):

        items_data = validated_data.pop("items")

        menu = Menu.objects.create(
            business=business,
            **validated_data
        )

        items = []

        for item in items_data:

            items.append(
                MenuItem(
                    business=business,
                    menu=menu,
                    name=item["name"],
                    description=item.get("description"),
                    price=item["price"],
                    image_url=item.get("image_url"),
                )
            )

        MenuItem.objects.bulk_create(items)

        return menu