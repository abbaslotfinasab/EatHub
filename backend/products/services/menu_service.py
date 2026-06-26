from django.db import transaction

from products.models import Menu, MenuItem


class MenuService:

    @staticmethod
    @transaction.atomic
    def create_menu_with_items(*, business, validated_data):

        items_data = validated_data.pop("items", [])

        menu = Menu.objects.create(
            business=business,
            **validated_data
        )

        items = [
            MenuItem(
                business=business,
                menu=menu,
                name=item["name"],
                description=item.get("description"),
                price=item["price"],
                image_url=item.get("image_url"),
                is_available=item.get("is_available", True),
            )
            for item in items_data
        ]

        MenuItem.objects.bulk_create(items)

        return menu

    @staticmethod
    @transaction.atomic
    def update_menu(menu, data):

        items_data = data.pop("items", None)

        for field in [
            "name",
            "category",
            "description",
            "sort_order",
            "is_active",
        ]:
            if field in data:
                setattr(menu, field, data[field])

        menu.save()

        # 🧠 فقط اگر items ارسال شده sync کن
        if items_data is None:
            return menu

        existing_items = {
            item.id: item
            for item in MenuItem.objects.filter(menu=menu)
        }

        incoming_ids = set()

        for item_data in items_data:

            item_id = item_data.get("id")

            if item_id and item_id in existing_items:
                item = existing_items[item_id]
            else:
                item = MenuItem(
                    menu=menu,
                    business=menu.business,
                )

            item.name = item_data["name"]
            item.description = item_data.get("description")
            item.price = item_data["price"]
            item.image_url = item_data.get("image_url")
            item.is_available = item_data.get("is_available", True)

            print("----------------")
            print(item_data)
            print(existing_items.keys())
            print(item_data.get("id"))

            item.save()

            incoming_ids.add(item.id)

        MenuItem.objects.filter(menu=menu).exclude(
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

        return MenuItem.objects.create(
            business=business,
            menu=menu,
            name=data["name"],
            description=data.get("description"),
            price=data["price"],
            image_url=data.get("image_url"),
            is_available=data.get("is_available", True),
        )

    @staticmethod
    @transaction.atomic
    def update_item(item, data):

        for field in [
            "name",
            "description",
            "price",
            "image_url",
            "is_available",
        ]:
            if field in data:
                setattr(item, field, data[field])

        item.save()

        return item

    @staticmethod
    @transaction.atomic
    def delete_item(item):

        item.delete()