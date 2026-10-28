from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from products.models import CustomerTransaction, OrderRefund

from products.models import CustomerAccount, OrderItem, Order, MenuItem
from django.db import IntegrityError, transaction
from decimal import Decimal

from products.services.wallet_service import WalletService
from products.services.order_inventory_service import OrderInventoryService
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
            Order.objects.select_for_update(),
            id=order_id,
            business=business,
        )

        has_order_transactions = CustomerTransaction.objects.filter(order=order).exists()
        wallet_settled = (
            order.payment_method == Order.PaymentMethod.CUSTOMER_ACCOUNT
            and (order.payment_status == Order.PaymentStatus.PAID or has_order_transactions)
        )
        if has_order_transactions and "customer" in validated_data and validated_data["customer"] != order.customer:
            raise ValidationError("The customer cannot be changed after wallet settlement.")
        financial_edit = bool(
            {"customer", "items", "discount", "tax"}.intersection(validated_data)
        )
        if (
            order.status == Order.Status.CANCELLED
            and order.payment_method == Order.PaymentMethod.CUSTOMER_ACCOUNT
            and order.payment_status == Order.PaymentStatus.PAID
            and financial_edit
        ):
            raise ValidationError(
                "Reopen a settled customer-account order before changing its total."
            )
        if (
            order.payment_status == Order.PaymentStatus.PAID
            and financial_edit
            and order.payment_method != Order.PaymentMethod.CUSTOMER_ACCOUNT
        ):
            raise ValidationError("Paid orders cannot be financially modified.")

        if "items" in validated_data and order.status != Order.Status.PENDING:
            raise ValidationError("Order items cannot be changed after inventory requirements are confirmed.")

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

        if "discount" in validated_data or "tax" in validated_data:
            order.total_amount = OrderService.calculate_total(
                subtotal=order.subtotal,
                discount=order.discount,
                tax=order.tax,
            )

        if items_data is None:
            order.save()
            if financial_edit and (wallet_settled or has_order_transactions):
                OrderService._reconcile_order_settlement(
                    order=order,
                    business=business,
                    target_amount=OrderService._wallet_target(order),
                    previous_payment_status=order.payment_status,
                )
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
        if financial_edit and (wallet_settled or has_order_transactions):
            OrderService._reconcile_order_settlement(
                order=order,
                business=business,
                target_amount=OrderService._wallet_target(order),
                previous_payment_status=order.payment_status,
            )
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
        from products.models import OrderItemRecipeSnapshot

        if order.status != Order.Status.PENDING or OrderItemRecipeSnapshot.objects.filter(order_id=order.pk).exists():
            raise ValidationError("Orders with inventory history must be cancelled, not deleted.")
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
            status=None,
            payment_status=None,
            payment_method=None,
            user=None,
    ):

        order = get_object_or_404(Order.objects.select_for_update(), id=order_id, business=business)
        previous_status = order.status
        previous_payment_status = order.payment_status
        previous_payment_method = order.payment_method
        for value, choices, field in (
            (status, Order.Status.values, "status"),
            (payment_status, Order.PaymentStatus.values, "payment_status"),
            (payment_method, Order.PaymentMethod.values, "payment_method"),
        ):
            if value is not None and value not in choices:
                raise ValidationError({field: "Unsupported value."})

        new_method = payment_method if payment_method is not None else previous_payment_method
        new_status = status if status is not None else previous_status
        new_payment_status = (
            payment_status if payment_status is not None else previous_payment_status
        )
        allowed_status_transitions = {
            Order.Status.PENDING: {
                Order.Status.PENDING, Order.Status.CONFIRMED,
                Order.Status.CANCELLED, Order.Status.FAILED,
            },
            Order.Status.CONFIRMED: {
                Order.Status.CONFIRMED, Order.Status.PREPARING,
                Order.Status.CANCELLED, Order.Status.FAILED,
            },
            Order.Status.PREPARING: {
                Order.Status.PREPARING, Order.Status.READY,
                Order.Status.CANCELLED, Order.Status.FAILED,
            },
            Order.Status.READY: {
                Order.Status.READY, Order.Status.COMPLETED,
                Order.Status.CANCELLED, Order.Status.FAILED,
            },
            Order.Status.COMPLETED: {Order.Status.COMPLETED},
            Order.Status.CANCELLED: {Order.Status.CANCELLED},
            Order.Status.FAILED: {Order.Status.FAILED},
        }
        if new_status not in allowed_status_transitions.get(previous_status, set()):
            raise ValidationError({
                "status": f"Transition from {previous_status} to {new_status} is not allowed."
            })
        if payment_status == Order.PaymentStatus.REFUNDED:
            raise ValidationError({
                "payment_status": "Use the refund operation to record and complete a refund."
            })
        if previous_payment_status == Order.PaymentStatus.REFUNDED and (
            payment_status is not None or payment_method is not None
        ):
            raise ValidationError(
                "A refunded payment cannot be changed through the status update endpoint."
            )
        method_changed = new_method != previous_payment_method
        has_wallet_history = CustomerTransaction.objects.filter(order=order).exists()

        if (
            method_changed
            and previous_payment_method == Order.PaymentMethod.CUSTOMER_ACCOUNT
            and new_method != Order.PaymentMethod.CUSTOMER_ACCOUNT
            and has_wallet_history
            and payment_status is None
        ):
            raise ValidationError({
                "payment_status": (
                    "Set the corrected payment status explicitly to reverse or confirm "
                    "the existing wallet settlement."
                )
            })

        if (
            new_status == Order.Status.CANCELLED
            and new_method == Order.PaymentMethod.CUSTOMER_ACCOUNT
            and payment_status == Order.PaymentStatus.PAID
            and (
                previous_payment_status != Order.PaymentStatus.PAID
                or not has_wallet_history
            )
        ):
            raise ValidationError(
                "A cancelled customer-account order cannot start a new wallet settlement."
            )

        # A payment-method switch does not prove payment on the new method.
        # Preserve paid only when the request explicitly confirms it.
        if (
            method_changed
            and (
                previous_payment_method == Order.PaymentMethod.CUSTOMER_ACCOUNT
                or new_method == Order.PaymentMethod.CUSTOMER_ACCOUNT
            )
            and payment_status is None
            and new_payment_status == Order.PaymentStatus.PAID
        ):
            new_payment_status = Order.PaymentStatus.PENDING

        order.status = new_status
        order.payment_method = new_method
        order.payment_status = new_payment_status
        # Persist the explicit paid state inside this transaction before the
        # authoritative wallet settlement service validates the order.
        order.save(update_fields=["status", "payment_status", "payment_method"])

        if new_status == Order.Status.CONFIRMED and previous_status != Order.Status.CONFIRMED:
            if user is None or user.pk is None:
                raise ValidationError("Confirming an order requires an authenticated actor.")
            OrderInventoryService.confirm(order=order, actor_id=user.pk)
        elif new_status == Order.Status.READY and previous_status != Order.Status.READY:
            OrderInventoryService.ensure_consumption_complete(order)
            if user is None or user.pk is None:
                raise ValidationError("Releasing order reservations requires an authenticated actor.")
            OrderInventoryService.release_remaining(
                order=order, actor_id=user.pk, reason="Order is ready; unused reserved stock released"
            )
        elif new_status in (Order.Status.CANCELLED, Order.Status.FAILED) and new_status != previous_status:
            if user is None or user.pk is None:
                raise ValidationError("Releasing order reservations requires an authenticated actor.")
            OrderInventoryService.release_remaining(
                order=order, actor_id=user.pk, reason=f"Order {new_status}"
            )
        elif new_status == Order.Status.COMPLETED and previous_status != Order.Status.COMPLETED:
            OrderInventoryService.ensure_consumption_complete(order)

        # Reconcile only when payment state or payment method was explicitly
        # changed. Completion alone never charges a wallet.
        reconciliation_requested = payment_status is not None or method_changed
        if reconciliation_requested and (
            previous_payment_method == Order.PaymentMethod.CUSTOMER_ACCOUNT
            or new_method == Order.PaymentMethod.CUSTOMER_ACCOUNT
            or has_wallet_history
        ):
            target_amount = OrderService._wallet_target(order)
            OrderService._reconcile_order_settlement(
                order=order,
                business=business,
                target_amount=target_amount,
                previous_payment_status=(
                    previous_payment_status
                    if previous_payment_method == Order.PaymentMethod.CUSTOMER_ACCOUNT
                    else None
                ),
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

            changed = []
            if order.status != previous_status:
                changed.append("وضعیت سفارش")
            if order.payment_status != previous_payment_status:
                changed.append("وضعیت پرداخت")
            if order.payment_method != previous_payment_method:
                changed.append("روش پرداخت")
            activity_description = (
                f"سفارش شماره {order.id} به‌روزرسانی شد: {', '.join(changed)}."
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
        """Explicitly settle an order to its current total, idempotently."""
        order = Order.objects.select_for_update().get(pk=order.pk, business=business)
        if order.payment_method != Order.PaymentMethod.CUSTOMER_ACCOUNT:
            raise ValidationError("Customer account payment method is required.")
        if order.payment_status == Order.PaymentStatus.REFUNDED:
            raise ValidationError("A refunded order cannot be charged again.")
        if (
            order.status == Order.Status.CANCELLED
            and order.payment_status != Order.PaymentStatus.PAID
        ):
            raise ValidationError(
                "A cancelled customer-account order cannot start a wallet settlement."
            )
        if not order.customer_id or order.customer.business_id != business.id:
            raise ValidationError("A customer belonging to this business is required.")
        previous_payment_status = order.payment_status
        order.payment_status = Order.PaymentStatus.PAID
        order.save(update_fields=["payment_status"])
        OrderService._reconcile_order_settlement(
            order=order,
            business=business,
            target_amount=OrderService._wallet_target(order),
            previous_payment_status=previous_payment_status,
        )
        return order

    @staticmethod
    def refund_order(
        *, business, order_id, user, idempotency_key, reason, reference="",
        amount=None, confirm_external_refund=False,
    ):
        try:
            return OrderService._refund_order_transaction(
                business=business,
                order_id=order_id,
                user=user,
                idempotency_key=idempotency_key,
                reason=reason,
                reference=reference,
                amount=amount,
                confirm_external_refund=confirm_external_refund,
            )
        except IntegrityError:
            # The key is unique across refunds. If a concurrent request claimed
            # it first, resolve it after this transaction has rolled back so
            # clients receive the original result or a clear conflict error.
            existing = OrderRefund.objects.filter(
                idempotency_key=idempotency_key
            ).first()
            if existing is None:
                raise
            return OrderService._get_idempotent_refund(
                existing=existing,
                business=business,
                order_id=order_id,
                reason=reason,
                reference=reference,
                amount=amount,
                confirm_external_refund=confirm_external_refund,
            )

    @staticmethod
    @transaction.atomic
    def _refund_order_transaction(
        *, business, order_id, user, idempotency_key, reason, reference="",
        amount=None, confirm_external_refund=False,
    ):
        """Record a full refund; cash/card completion is an explicit manual attestation."""
        existing = OrderRefund.objects.select_for_update().filter(
            idempotency_key=idempotency_key
        ).first()
        if existing:
            return OrderService._get_idempotent_refund(
                existing=existing,
                business=business,
                order_id=order_id,
                reason=reason,
                reference=reference,
                amount=amount,
                confirm_external_refund=confirm_external_refund,
            )

        order = get_object_or_404(
            Order.objects.select_for_update(), id=order_id, business=business
        )
        existing = OrderRefund.objects.select_for_update().filter(
            idempotency_key=idempotency_key
        ).first()
        if existing:
            return OrderService._get_idempotent_refund(
                existing=existing,
                business=business,
                order_id=order.id,
                reason=reason,
                reference=reference,
                amount=amount,
                confirm_external_refund=confirm_external_refund,
            )

        if order.payment_status == Order.PaymentStatus.REFUNDED:
            raise ValidationError("This payment is already refunded.")
        if order.payment_status != Order.PaymentStatus.PAID:
            raise ValidationError("Only a confirmed paid order can be refunded.")
        if not reason or not reason.strip():
            raise ValidationError({"reason": "A refund reason is required."})

        settlement_amount, _ = OrderService._validated_order_settlement(
            order=order, business=business
        )
        wallet_method = order.payment_method == Order.PaymentMethod.CUSTOMER_ACCOUNT
        if wallet_method:
            if not order.customer_id or settlement_amount <= 0:
                raise ValidationError(
                    "No valid outstanding wallet settlement exists to refund."
                )
            refund_amount = settlement_amount
            if amount is not None and Decimal(str(amount)) != refund_amount:
                raise ValidationError({"amount": "Wallet refunds use the outstanding ledger amount."})
        else:
            raise ValidationError({
                "payment_method": (
                    "A cash/card refund cannot be recorded because this application has no "
                    "immutable payment record to verify the amount. Record the manual refund "
                    "outside EatHub; do not mark it refunded here."
                )
            })

        refund = OrderRefund.objects.create(
            order=order,
            business=business,
            customer=order.customer,
            payment_method=order.payment_method,
            amount=refund_amount,
            reason=reason.strip(),
            reference=(reference or "").strip(),
            idempotency_key=idempotency_key,
            actor=user,
        )

        if wallet_method:
            OrderService._reconcile_order_settlement(
                order=order,
                business=business,
                target_amount=Decimal("0"),
                previous_payment_status=Order.PaymentStatus.PAID,
                refund=refund,
            )

        # Refunds cancel the order through this path rather than update_status;
        # release only the outstanding hold. Posted consumption remains in the
        # append-only inventory ledger. This joins the refund transaction so a
        # failed release also rolls back the refund and wallet reconciliation.
        OrderInventoryService.release_remaining(
            order=order,
            actor_id=user.pk if user is not None else None,
            reason="Order refunded; remaining reservation released",
        )

        order.status = Order.Status.CANCELLED
        order.payment_status = Order.PaymentStatus.REFUNDED
        order.save(update_fields=["status", "payment_status"])
        ActivityLogService.record(
            business=business,
            user=user,
            action=ActivityLog.Action.ORDER_REFUNDED,
            title="بازپرداخت سفارش ثبت شد",
            description=(
                f"سفارش شماره {order.id}؛ مبلغ {refund_amount}؛ "
                f"روش {order.payment_method}؛ علت: {refund.reason}؛ "
                f"مرجع: {refund.reference or 'ندارد'}."
            ),
            entity_type="order",
            entity_id=order.id,
        )
        return refund

    @staticmethod
    def _get_idempotent_refund(
        *, existing, business, order_id, reason, reference, amount,
        confirm_external_refund,
    ):
        if existing.business_id != business.id or existing.order_id != order_id:
            raise ValidationError({"idempotency_key": "This key belongs to another refund."})

        amount_matches = (
            Decimal(str(amount)) == existing.amount
            if amount is not None
            else existing.payment_method == Order.PaymentMethod.CUSTOMER_ACCOUNT
        )
        same_request = (
            existing.reason == (reason or "").strip()
            and existing.reference == (reference or "").strip()
            and amount_matches
            and confirm_external_refund
            == (existing.payment_method != Order.PaymentMethod.CUSTOMER_ACCOUNT)
        )
        if not same_request:
            raise ValidationError({
                "idempotency_key": "This key was already used with different refund parameters."
            })
        return existing

    @staticmethod
    def _wallet_target(order):
        if (
            order.payment_method == Order.PaymentMethod.CUSTOMER_ACCOUNT
            and order.payment_status == Order.PaymentStatus.PAID
        ):
            amount = Decimal(str(order.total_amount))
            if amount <= 0:
                raise ValidationError("Order total must be positive for wallet settlement.")
            return amount
        return Decimal("0")

    @staticmethod
    @transaction.atomic
    def _reconcile_order_settlement(
        *, order, business, target_amount, previous_payment_status=None, refund=None
    ):
        order = Order.objects.select_for_update().get(pk=order.pk, business=business)
        target_amount = Decimal(str(target_amount))
        if target_amount < 0:
            raise ValidationError("Wallet settlement target cannot be negative.")

        settled_amount, transactions = OrderService._validated_order_settlement(
            order=order, business=business
        )
        if not order.customer_id and (target_amount > 0 or transactions):
            raise ValidationError(
                "A customer belonging to this business is required to reconcile this wallet ledger."
            )
        if not order.customer_id:
            return order

        if settled_amount < 0:
            raise ValidationError(
                "Order wallet credits exceed its recorded charges. Review the order ledger before retrying."
            )
        if (
            previous_payment_status == Order.PaymentStatus.PAID
            and settled_amount == 0
            and target_amount > 0
        ):
            raise ValidationError(
                "Order is marked paid but has no valid wallet settlement. Review its ledger before retrying."
            )

        difference = target_amount - settled_amount
        if difference > 0:
            WalletService.settle_order(
                business=business,
                order_id=order.id,
            )
        elif difference < 0:
            if refund is None:
                raise ValidationError(
                    "Reducing an existing wallet settlement requires the explicit refund operation."
                )
            WalletService.record_refund_credit(
                business=business,
                refund=refund,
                description=f"Order #{order.id} settlement credit",
            )

        return order

    @staticmethod
    def _validated_order_settlement(*, order, business):
        if not order.customer_id:
            transactions = list(
                CustomerTransaction.objects.filter(order=order).order_by("id")
            )
            return Decimal("0"), transactions
        if order.customer.business_id != business.id:
            raise ValidationError("A customer belonging to this business is required.")

        account = CustomerAccount.objects.select_for_update().filter(
            customer_id=order.customer_id
        ).first()
        if account and account.business_id != business.id:
            raise ValidationError("Customer account belongs to a different business.")

        account_history = (
            WalletService._validated_balance_history(account) if account else []
        )

        transactions = [
            entry for entry in account_history if entry.order_id == order.id
        ]
        if CustomerTransaction.objects.filter(order=order).exclude(
            account_id=account.id if account else None
        ).exists():
            raise ValidationError("Order wallet entries belong to another customer account.")
        if not account and CustomerTransaction.objects.filter(order=order).exists():
            raise ValidationError("Order wallet entries have no customer account.")

        settled_amount = Decimal("0")
        for txn in transactions:
            if (
                not txn.is_order_settlement
                or not txn.is_order_settlement_verified
                or txn.account_id != account.id
                or account.customer_id != order.customer_id
                or account.business_id != business.id
                or txn.amount <= 0
                or txn.type not in (CustomerTransaction.Type.DEBIT, CustomerTransaction.Type.CREDIT)
            ):
                raise ValidationError(
                    "Order wallet ledger is inconsistent or unclassified. Review the order ledger before retrying."
                )
            if txn.type == CustomerTransaction.Type.CREDIT:
                if not txn.refund_id:
                    raise ValidationError(
                        "An order settlement credit has no refund record. Review the order ledger before retrying."
                    )
                refund = txn.refund
                if (
                    refund.order_id != order.id
                    or refund.business_id != business.id
                    or refund.customer_id != order.customer_id
                    or refund.payment_method != Order.PaymentMethod.CUSTOMER_ACCOUNT
                    or txn.amount != refund.amount
                    or CustomerTransaction.objects.filter(refund_id=refund.id)
                    .exclude(pk=txn.pk)
                    .exists()
                ):
                    raise ValidationError(
                        "The order refund ledger does not match its refund record. Review it before retrying."
                    )
            elif txn.refund_id:
                raise ValidationError(
                    "A refund record is linked to a non-credit order transaction. Review the order ledger before retrying."
                )
            if txn.type == CustomerTransaction.Type.DEBIT:
                settled_amount += Decimal(str(txn.amount))
            else:
                settled_amount -= Decimal(str(txn.amount))

        if settled_amount < 0:
            raise ValidationError(
                "Order wallet credits exceed its recorded charges. Review the order ledger before retrying."
            )
        return settled_amount, transactions
