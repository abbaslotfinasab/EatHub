from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from products.models import CustomerTransaction

from products.models import OrderItem, Order, MenuItem
from django.db import transaction
from decimal import Decimal

from products.services.wallet_service import WalletService
from core.models import ActivityLog
from core.services.ActivityLogService import ActivityLogService


class OrderService:

    @staticmethod
    @transaction.atomic
    def create_order(*, business, validated_data, user=None):

        items_data = validated_data.pop("items")
        customer = validated_data.get("customer")
        if customer and customer.business_id != business.id:
            raise ValidationError("Customer does not belong to this business.")

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

        ActivityLogService.record(
            business=business,
            user=user,
            action=ActivityLog.Action.ORDER_CREATED,
            title="سفارش جدید ثبت شد",
            description=f"سفارش شماره {order.id} ثبت شد.",
            entity_type="order",
            entity_id=order.id,
        )

        return order

    @staticmethod
    @transaction.atomic
    def update_order(*, business, order_id, validated_data, user=None):

        order = get_object_or_404(
            Order,
            id=order_id,
            business=business,
        )

        order = Order.objects.select_for_update().get(pk=order.pk)
        if order.payment_status == Order.PaymentStatus.PAID and {"customer", "items", "discount", "tax"}.intersection(validated_data):
            raise ValidationError("Paid orders cannot be financially modified.")

        items_data = validated_data.pop("items", None)

        customer = validated_data.get("customer", order.customer)
        if customer and customer.business_id != business.id:
            raise ValidationError("Customer does not belong to this business.")

        order.customer = customer
        for field in ("table", "order_type", "notes"):
            if field in validated_data:
                setattr(order, field, validated_data[field])

        order.discount = validated_data.get(
            "discount",
            order.discount,
        ) or Decimal("0")

        order.tax = validated_data.get(
            "tax",
            order.tax,
        ) or Decimal("0")

        if items_data is None:
            order.save()
            ActivityLogService.record(
                business=business,
                user=user,
                action=ActivityLog.Action.UPDATE,
                title="سفارش ویرایش شد",
                description=f"سفارش شماره {order.id} ویرایش شد.",
                entity_type="order",
                entity_id=order.id,
            )
            return order

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
        ActivityLogService.record(
            business=business,
            user=user,
            action=ActivityLog.Action.UPDATE,
            title="سفارش ویرایش شد",
            description=f"سفارش شماره {order.id} ویرایش شد.",
            entity_type="order",
            entity_id=order.id,
        )
        return order

    @staticmethod
    @transaction.atomic
    def delete_order(order, user=None):
        order = Order.objects.select_for_update().get(pk=order.pk)
        has_transactions = CustomerTransaction.objects.filter(order=order).exists()
        safely_deletable_payment_statuses = (
            Order.PaymentStatus.PENDING,
            Order.PaymentStatus.UNPAID,
            Order.PaymentStatus.FAILED,
        )
        if order.payment_status not in safely_deletable_payment_statuses or has_transactions:
            raise ValidationError(
                "Only unsettled orders without wallet transactions can be deleted."
            )
        ActivityLogService.record(
            business=order.business,
            user=user,
            action=ActivityLog.Action.DELETE,
            title="سفارش حذف شد",
            description=f"سفارش شماره {order.id} حذف شد.",
            entity_type="order",
            entity_id=order.id,
        )
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
            user=None,
    ):

        order = get_object_or_404(Order.objects.select_for_update(), id=order_id, business=business)
        previous_status = order.status
        previous_payment_status = order.payment_status
        previous_payment_method = order.payment_method

        if order.payment_status == Order.PaymentStatus.PAID and payment_method and payment_method != order.payment_method:
            raise ValidationError("Payment method cannot be changed after payment.")

        order.status = status

        if payment_method is not None:
            order.payment_method = payment_method

        if (
            order.payment_method == Order.PaymentMethod.CUSTOMER_ACCOUNT
            and status == Order.Status.COMPLETED
            and payment_status is not None
            and payment_status != Order.PaymentStatus.PAID
        ):
            raise ValidationError(
                "A completed customer-account order cannot request a non-paid payment status."
            )

        # Persist the locked order's requested method before pay_order reloads it.
        # The surrounding atomic block rolls this write back if payment fails.
        order.save(update_fields=["status", "payment_method"])

        if payment_status == Order.PaymentStatus.PAID:
            if order.payment_method != Order.PaymentMethod.CUSTOMER_ACCOUNT:
                order.payment_status = Order.PaymentStatus.PAID
        elif payment_status is not None:
            if order.payment_status == Order.PaymentStatus.PAID:
                raise ValidationError("Paid orders cannot be marked unpaid or refunded here.")
            order.payment_status = payment_status

        # Charge on an explicit wallet-paid request or the legacy completion flow.
        # Also validate every already-paid wallet order so inconsistent historical
        # state fails closed on later status requests.
        if (order.payment_method == Order.PaymentMethod.CUSTOMER_ACCOUNT and (
                payment_status == Order.PaymentStatus.PAID
                or order.payment_status == Order.PaymentStatus.PAID
                or status == Order.Status.COMPLETED
        )):
            OrderService.pay_order(order=order, business=business)

        order.save(
            update_fields=[
                "status",
                "payment_status",
                "payment_method",
            ]
        )

        if (
            order.status != previous_status
            or order.payment_status != previous_payment_status
            or order.payment_method != previous_payment_method
        ):
            if order.status == Order.Status.COMPLETED and order.status != previous_status:
                action = ActivityLog.Action.ORDER_COMPLETED
                title = "سفارش تکمیل شد"
            elif order.status == Order.Status.CANCELLED and order.status != previous_status:
                action = ActivityLog.Action.ORDER_CANCELLED
                title = "سفارش لغو شد"
            else:
                action = ActivityLog.Action.UPDATE
                title = "سفارش یا پرداخت به‌روزرسانی شد"

            activity_description = (
                f"وضعیت سفارش شماره {order.id}: {previous_status} ← {order.status}."
                if order.status != previous_status
                else f"اطلاعات پرداخت سفارش شماره {order.id} به‌روزرسانی شد."
            )

            ActivityLogService.record(
                business=business,
                user=user,
                action=action,
                title=title,
                description=activity_description,
                entity_type="order",
                entity_id=order.id,
            )

        return order

    @staticmethod
    @transaction.atomic
    def pay_order(*, order, business):
        """Charge an order's persisted total once inside the caller's transaction."""
        order = Order.objects.select_for_update().get(pk=order.pk, business=business)
        if order.payment_method != Order.PaymentMethod.CUSTOMER_ACCOUNT:
            raise ValidationError("Customer account payment method is required.")
        if order.payment_status == Order.PaymentStatus.REFUNDED:
            raise ValidationError("A refunded order cannot be charged again.")
        if not order.customer_id or order.customer.business_id != business.id:
            raise ValidationError("A customer belonging to this business is required.")
        if order.total_amount <= 0:
            raise ValidationError("Order total must be positive.")
        existing_debits = CustomerTransaction.objects.filter(
            order=order,
            type=CustomerTransaction.Type.DEBIT,
        )
        if order.payment_status == Order.PaymentStatus.PAID:
            debit = existing_debits.first()
            if (debit is None or existing_debits.count() != 1
                    or debit.amount != order.total_amount
                    or debit.account.customer_id != order.customer_id
                    or debit.account.business_id != business.id):
                raise ValidationError(
                    "Paid order ledger does not match; manual reconciliation is required."
                )
            return order
        if existing_debits.exists():
            raise ValidationError("Order already has a wallet debit but is not marked paid.")
        WalletService.debit(
            business=business,
            customer=order.customer,
            amount=order.total_amount,
            order=order,
            description=f"Order #{order.id}",
        )
        order.payment_status = Order.PaymentStatus.PAID
        order.save(update_fields=["payment_status"])
        return order
