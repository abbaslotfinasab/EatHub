from django.shortcuts import get_object_or_404

from products.models import OrderItem, Order, MenuItem
from django.db import transaction
from decimal import Decimal

from products.services.wallet_service import WalletService


class OrderService:

    @staticmethod
    @transaction.atomic
    def create_order(*, business, validated_data):

        items_data = validated_data.pop("items")
        customer = validated_data.get("customer")

        order = Order.objects.create(
            business=business,
            customer=customer,
            table=validated_data["table"],
            order_type=validated_data["order_type"],
            notes=validated_data.get("notes"),
            status=Order.Status.PENDING,
            subtotal=Decimal("0"),
            discount=validated_data.get("discount") or Decimal("0"),
            tax=validated_data.get("tax") or Decimal("0"),
            total_amount=Decimal("0"),
        )

        subtotal = Decimal("0")

        # 🔥 FIX: batch fetch (avoid N+1)
        menu_item_ids = [i["menu_item_id"] for i in items_data]

        menu_items = MenuItem.objects.filter(
            id__in=menu_item_ids,
            business=business
        ).in_bulk()

        for item in items_data:

            menu_item = menu_items.get(item["menu_item_id"])

            if not menu_item:
                raise ValueError("Invalid menu item")

            quantity = item["quantity"]
            unit_price = menu_item.price
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

        discount = order.discount or Decimal("0")
        tax = order.tax or Decimal("0")

        order.subtotal = subtotal
        total = OrderService.calculate_total(
            subtotal=subtotal,
            discount=discount,
            tax=tax,
        )

        order.total_amount = total

        order.save(
            update_fields=[
                "subtotal",
                "total_amount",
            ]
        )

        return order

    @staticmethod
    @transaction.atomic
    def update_order(*, business, order_id, validated_data):

        order = get_object_or_404(
            Order,
            id=order_id,
            business=business,
        )

        old_total = order.total_amount

        items_data = validated_data.pop("items")

        customer = validated_data.get("customer")

        order.customer = customer
        order.order_type = validated_data["order_type"]
        order.notes = validated_data.get("notes")

        order.discount = validated_data.get(
            "discount",
            order.discount,
        ) or Decimal("0")

        order.tax = validated_data.get(
            "tax",
            order.tax,
        ) or Decimal("0")

        # حذف آیتم‌های قبلی
        order.items.all().delete()

        subtotal = Decimal("0")

        menu_item_ids = [
            item["menu_item_id"]
            for item in items_data
        ]

        menu_items = MenuItem.objects.filter(
            business=business,
            id__in=menu_item_ids,
        ).in_bulk()

        for item in items_data:

            menu_item = menu_items.get(
                item["menu_item_id"]
            )

            if not menu_item:
                raise ValueError("Invalid menu item")

            quantity = item["quantity"]

            unit_price = menu_item.price

            total_price = quantity * unit_price

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

        order.subtotal = subtotal

        order.total_amount = OrderService.calculate_total(
            subtotal=subtotal,
            discount=order.discount,
            tax=order.tax,
        )

        order.save()

    @staticmethod
    @transaction.atomic
    def delete_order(order):

        order.delete()

    @staticmethod
    def calculate_total(subtotal: Decimal, discount: Decimal, tax: Decimal) -> Decimal:
        return subtotal - discount + tax

    @staticmethod
    @transaction.atomic
    def update_status(
            *,
            business,
            order_id,
            status,
            payment_status=None,
            payment_method=None,
    ):

        order = get_object_or_404(
            Order,
            id=order_id,
            business=business,
        )

        old_status = order.status
        old_payment_status = order.payment_status

        order.status = status

        if payment_method is not None:
            order.payment_method = payment_method

        if payment_status is not None:
            order.payment_status = payment_status

        # =====================================
        # CUSTOMER ACCOUNT PAYMENT
        # =====================================

        should_debit = (
                old_status != Order.Status.COMPLETED
                and status == Order.Status.COMPLETED
                and order.payment_method == Order.PaymentMethod.CUSTOMER_ACCOUNT
                and old_payment_status != Order.PaymentStatus.PAID
                and order.customer
        )

        if should_debit:
            account = WalletService.get_or_create_account(
                business=business,
                customer=order.customer,
            )

            WalletService.debit(
                business=business,
                customer=order.customer,
                amount=order.total_amount,
                order=order,
                description=f"Order #{order.id}",
            )

            order.payment_status = (
                Order.PaymentStatus.PAID
            )

        order.save(
            update_fields=[
                "status",
                "payment_status",
                "payment_method",
            ]
        )

        return order