from django.shortcuts import get_object_or_404

from products.models import OrderItem, Order, MenuItem
from django.db import transaction
from decimal import Decimal

from products.services.customer_service import CustomerService
from products.services.wallet_service import WalletService


class OrderService:

    @staticmethod
    @transaction.atomic
    def create_order(*, business, validated_data):

        items_data = validated_data.pop("items")
        customer = validated_data.get("customer")

        account = None

        if customer:
            account = WalletService.get_account(
                business=business,
                customer=customer,
            )

        order = Order.objects.create(
            business=business,
            customer=customer,
            table= validated_data["table"],
            order_type=validated_data["order_type"],
            notes=validated_data.get("notes"),
            status=Order.Status.PENDING,
            subtotal=Decimal("0"),
            discount=validated_data.get("discount") or Decimal("0"),
            tax = validated_data.get("tax") or Decimal("0"),
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

        order.refresh_from_db()
        print(order.table)

        # =========================
        # 💳 DEBIT CUSTOMER ACCOUNT
        # =========================
        if account:
            WalletService.debit(
                account=account,
                amount=order.total_amount,
                order=order,
                description=f"Order #{order.id}",
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

        customer_name = validated_data.get("customer_name")
        customer_phone = validated_data.get("customer_phone")

        customer = None
        account = None

        if customer_phone:
            customer = CustomerService.get_or_create_customer(
                business=business,
                name=customer_name,
                phone=customer_phone,
            )

            account = WalletService.get_account(
                business=business,
                customer=customer,
            )

        order.customer = customer
        order.customer_name = customer.name if customer else "Guest"
        order.customer_phone = customer_phone
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

        # -----------------------------
        # اصلاح مانده حساب مشتری
        # -----------------------------
        if account:

            difference = order.total_amount - old_total

            if difference > 0:

                WalletService.debit(
                    account=account,
                    amount=difference,
                    order=order,
                    description=f"Update Order #{order.id}",
                )

            elif difference < 0:

                WalletService.credit(
                    account=account,
                    amount=abs(difference),
                    order=order,
                    description=f"Update Order #{order.id}",
                )

        return order

    @staticmethod
    @transaction.atomic
    def delete_order(order):

        if order.customer:
            WalletService.credit(
                account=order.customer.account,
                amount=order.total_amount,
                order=order,
                description=f"Delete Order #{order.id}",
            )

        order.delete()

    @staticmethod
    def calculate_total(subtotal: Decimal, discount: Decimal, tax: Decimal) -> Decimal:
        return subtotal - discount + tax
