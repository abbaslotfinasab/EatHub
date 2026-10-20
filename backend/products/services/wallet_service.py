from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from products.models import (
    Customer,
    CustomerAccount,
    CustomerTransaction,
    Order,
    OrderRefund,
)


class WalletService:

    @staticmethod
    def get_or_create_account(
        *,
        business,
        customer: Customer,
    ) -> CustomerAccount:

        if customer.business_id != business.id:
            raise ValidationError("Customer does not belong to this business.")

        account, _ = CustomerAccount.objects.get_or_create(
            customer=customer,
            defaults={
                "business": business,
                "ledger_opening_balance": Decimal("0"),
                # Accounts created through this service begin at the model's
                # known zero balance. Migrated/pre-existing rows stay unverified.
                "ledger_opening_balance_verified": True,
            },
        )
        if account.business_id != business.id:
            raise ValidationError("Customer account does not belong to this business.")

        return account

    @staticmethod
    @transaction.atomic
    def credit(
        *,
        business,
        customer: Customer,
        amount: Decimal,
        description: str = "",
        order: Order | None = None,
        refund: OrderRefund | None = None,
    ) -> CustomerTransaction:

        if order is not None or refund is not None:
            raise ValidationError(
                "Order-linked credits must use the dedicated refund-credit operation."
            )

        account = WalletService.get_or_create_account(
            business=business,
            customer=customer,
        )

        account = (
            CustomerAccount.objects
            .select_for_update()
            .get(pk=account.pk)
        )
        WalletService._validated_balance_history(account)

        amount = Decimal(amount)
        if amount <= 0:
            raise ValidationError("Amount must be positive.")
        account.balance += amount

        account.save(
            update_fields=["balance"]
        )

        return CustomerTransaction.objects.create(
            account=account,
            type=CustomerTransaction.Type.CREDIT,
            amount=amount,
            balance_after=account.balance,
            description=description,
            is_order_settlement=False,
            is_order_settlement_verified=False,
        )

    @staticmethod
    @transaction.atomic
    def record_refund_credit(*, business, refund: OrderRefund, description=""):
        """Create the sole verified order-linked credit from refund evidence."""
        if refund is None or refund.pk is None:
            raise ValidationError("A persisted refund record is required.")
        refund = OrderRefund.objects.select_for_update().get(
            pk=refund.pk,
            business=business,
        )
        order = Order.objects.select_for_update().get(
            pk=refund.order_id,
            business=business,
        )
        if (
            order.payment_status != Order.PaymentStatus.PAID
            or order.payment_method != Order.PaymentMethod.CUSTOMER_ACCOUNT
            or refund.payment_method != Order.PaymentMethod.CUSTOMER_ACCOUNT
            or refund.customer_id != order.customer_id
            or not order.customer_id
            or order.customer.business_id != business.id
        ):
            raise ValidationError("Refund does not match a paid customer-account order.")

        from products.services.order_service import OrderService

        settled_amount, _ = OrderService._validated_order_settlement(
            order=order,
            business=business,
        )
        if settled_amount <= 0 or refund.amount != settled_amount:
            raise ValidationError(
                "Refund amount does not match the validated outstanding settlement."
            )

        account = WalletService.get_or_create_account(
            business=business,
            customer=order.customer,
        )
        account = CustomerAccount.objects.select_for_update().get(pk=account.pk)
        WalletService._validated_balance_history(account)
        account.balance += refund.amount
        account.save(update_fields=["balance"])
        return CustomerTransaction.objects.create(
            account=account,
            order=order,
            type=CustomerTransaction.Type.CREDIT,
            amount=refund.amount,
            balance_after=account.balance,
            description=description,
            is_order_settlement=True,
            is_order_settlement_verified=True,
            refund=refund,
        )

    @staticmethod
    @transaction.atomic
    def debit(
        *,
        business,
        customer: Customer,
        amount: Decimal,
        description: str = "",
        order: Order | None = None,
    ) -> CustomerTransaction:

        WalletService._validate_order_reference(business, customer, order)

        if order is not None:
            order = Order.objects.select_for_update().get(pk=order.pk, business=business)
            if order.customer_id != customer.id:
                raise ValidationError("Order does not belong to this customer and business.")
            if CustomerTransaction.objects.filter(
                order=order,
                type=CustomerTransaction.Type.DEBIT,
            ).exists():
                raise ValidationError("Order already has a wallet payment debit.")

        account = WalletService.get_or_create_account(
            business=business,
            customer=customer,
        )

        account = (
            CustomerAccount.objects
            .select_for_update()
            .get(pk=account.pk)
        )
        WalletService._validated_balance_history(account)

        amount = Decimal(amount)
        if amount <= 0:
            raise ValidationError("Amount must be positive.")
        return WalletService._record_debit(
            account=account,
            order=order,
            amount=amount,
            description=description,
        )

    @staticmethod
    @transaction.atomic
    def settle_order(*, business, order_id) -> CustomerTransaction:
        """Debit only the amount required to settle a persisted paid wallet order.

        Ordinary wallet debits cannot set the settlement marker. This narrow
        operation derives the amount from the paid order and its validated
        settlement entries instead of accepting a caller-provided amount/flag.
        """
        order = Order.objects.select_for_update().get(
            pk=order_id,
            business=business,
        )
        if (
            order.payment_method != Order.PaymentMethod.CUSTOMER_ACCOUNT
            or order.payment_status != Order.PaymentStatus.PAID
            or order.status == Order.Status.CANCELLED
        ):
            raise ValidationError("Only an active, paid customer-account order can be settled.")
        if not order.customer_id or order.customer.business_id != business.id:
            raise ValidationError("A customer belonging to this business is required.")

        account = WalletService.get_or_create_account(
            business=business,
            customer=order.customer,
        )
        account = CustomerAccount.objects.select_for_update().get(pk=account.pk)
        # Keep the full account-history and order-ledger validator authoritative
        # even if this wallet operation is called outside OrderService.
        from products.services.order_service import OrderService

        settled_amount, _ = OrderService._validated_order_settlement(
            order=order,
            business=business,
        )
        difference = Decimal(str(order.total_amount)) - settled_amount
        if difference <= 0:
            raise ValidationError("The order has no positive outstanding settlement amount.")

        account.balance -= difference
        account.save(update_fields=["balance"])
        return CustomerTransaction.objects.create(
            account=account,
            order=order,
            type=CustomerTransaction.Type.DEBIT,
            amount=difference,
            balance_after=account.balance,
            description=f"Order #{order.id} settlement debit",
            is_order_settlement=True,
            is_order_settlement_verified=True,
        )

    @staticmethod
    def _record_debit(*, account, order, amount, description):
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValidationError("Amount must be positive.")
        account.balance -= amount
        account.save(update_fields=["balance"])
        return CustomerTransaction.objects.create(
            account=account,
            order=order,
            type=CustomerTransaction.Type.DEBIT,
            amount=amount,
            balance_after=account.balance,
            description=description,
            is_order_settlement=False,
            is_order_settlement_verified=False,
        )

    @staticmethod
    @transaction.atomic
    def adjust(
        *,
        business,
        customer: Customer,
        amount: Decimal,
        description: str = "",
    ) -> CustomerTransaction:

        account = WalletService.get_or_create_account(
            business=business,
            customer=customer,
        )

        account = (
            CustomerAccount.objects
            .select_for_update()
            .get(pk=account.pk)
        )
        WalletService._validated_balance_history(account)

        amount = Decimal(amount)
        account.balance = amount

        account.save(
            update_fields=["balance"]
        )

        return CustomerTransaction.objects.create(
            account=account,
            type=CustomerTransaction.Type.ADJUST,
            amount=amount,
            balance_after=account.balance,
            description=description,
        )

    @staticmethod
    def get_balance(
        *,
        business,
        customer: Customer,
    ) -> Decimal:

        account = WalletService.get_or_create_account(
            business=business,
            customer=customer,
        )

        return account.balance

    @staticmethod
    def _validated_balance_history(account):
        """Validate snapshots from a known opening balance; never infer a legacy baseline."""
        if not account.ledger_opening_balance_verified:
            raise ValidationError(
                "Wallet opening balance is unverified. Review and reconcile this legacy account before changing its balance."
            )

        history = list(
            CustomerTransaction.objects.select_for_update()
            .filter(account=account)
            .order_by("id")
        )
        expected_balance = Decimal(str(account.ledger_opening_balance))
        for entry in history:
            if entry.type == CustomerTransaction.Type.DEBIT:
                if entry.amount <= 0:
                    raise ValidationError("Wallet history contains a nonpositive debit.")
                expected_balance -= entry.amount
            elif entry.type == CustomerTransaction.Type.CREDIT:
                if entry.amount <= 0:
                    raise ValidationError("Wallet history contains a nonpositive credit.")
                expected_balance += entry.amount
            elif entry.type == CustomerTransaction.Type.ADJUST:
                # Existing WalletService.adjust semantics set the balance to amount.
                expected_balance = entry.amount
            else:
                raise ValidationError("Wallet history contains an unsupported transaction type.")

            if entry.balance_after != expected_balance:
                raise ValidationError(
                    "Wallet balance history is inconsistent. Review the account ledger before retrying."
                )

        if account.balance != expected_balance:
            raise ValidationError(
                "Wallet balance does not match its opening balance and ledger history. Review the account before retrying."
            )
        return history

    @staticmethod
    def _validate_order_reference(business, customer, order):
        if order is not None and (
            order.business_id != business.id or order.customer_id != customer.id
        ):
            raise ValidationError("Order does not belong to this customer and business.")
