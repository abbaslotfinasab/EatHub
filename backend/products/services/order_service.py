from products.models import OrderItem, Order, MenuItem
from django.db import transaction
from decimal import Decimal


class OrderService:

    @staticmethod
    @transaction.atomic
    def create_order(*, business, validated_data):

        items_data = validated_data.pop("items")

        # 1. create order
        order = Order.objects.create(
            business=business,
            customer_name=validated_data.get("customer_name") or "Guest",
            customer_phone=validated_data.get("customer_phone"),
            order_type=validated_data["order_type"],
            notes=validated_data.get("notes"),
            status=Order.Status.PENDING,
            subtotal=0,
            discount=0,
            tax=0,
            total_amount=0,
        )

        subtotal = Decimal("0")

        # 2. create items (snapshot pattern)
        for item in items_data:

            menu_item = MenuItem.objects.get(
                id=item["menu_item_id"],
                business=business
            )

            unit_price = menu_item.price
            quantity = item["quantity"]

            total_price = unit_price * quantity

            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                menu_item_name=menu_item.name,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
                notes=item.get("notes"),
            )

            subtotal += total_price

        # 3. totals
        order.subtotal = subtotal
        order.total_amount = subtotal
        order.save()

        return order