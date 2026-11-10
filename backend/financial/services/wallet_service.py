from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from customer.models import Customer
from financial.models import CustomerAccount, CustomerTransaction, OrderRefund


CUSTOMER_ACCOUNT_PAYMENT_METHOD = "customer_account"


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
    def record_refund_credit(
        *, business, refund: OrderRefund, expected_settled_amount=None, description=""
    ):
        """Post a refund credit after Sales has validated the refund command.

        Financial revalidates its own ledger and refund evidence without loading
        or depending on the Sales Order model or OrderService.
        """
        if refund is None or refund.pk is None:
            raise ValidationError("A persisted refund record is required.")
        refund = OrderRefund.objects.select_for_update().get(
            pk=refund.pk,
            business=business,
        )
        if (
            expected_settled_amount is None
            or Decimal(str(expected_settled_amount)) != refund.amount
            or refund.payment_method != CUSTOMER_ACCOUNT_PAYMENT_METHOD
            or not refund.customer_id
        ):
            raise ValidationError(
                "Refund amount does not match the validated outstanding settlement."
            )

        settled_amount, _ = WalletService.validated_order_settlement(
            business=business,
            order_id=refund.order_id,
            customer_id=refund.customer_id,
        )
        if settled_amount != Decimal(str(expected_settled_amount)):
            raise ValidationError(
                "Refund amount does not match the validated outstanding settlement."
            )

        customer = Customer.objects.get(pk=refund.customer_id, business=business)
        account = WalletService.get_or_create_account(
            business=business,
            customer=customer,
        )
        account = CustomerAccount.objects.select_for_update().get(pk=account.pk)
        WalletService._validated_balance_history(account)
        account.balance += refund.amount
        account.save(update_fields=["balance"])
        return CustomerTransaction.objects.create(
            account=account,
            order_id=refund.order_id,
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
        order=None,
    ) -> CustomerTransaction:

        WalletService._validate_order_reference(business, customer, order)

        if order is not None:
            if order.business_id != business.id or order.customer_id != customer.id:
                raise ValidationError("Order does not belong to this customer and business.")
            if CustomerTransaction.objects.filter(
                order_id=order.pk,
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
            order_id=order.pk if order is not None else None,
            amount=amount,
            description=description,
        )

    @staticmethod
    @transaction.atomic
    def settle_order(
        *, business, order_id, customer: Customer, amount, expected_settled_amount
    ) -> CustomerTransaction:
        """Record a Sales-validated settlement delta in the wallet ledger.

        Order state and target amount are owned and validated by Sales. This
        operation only verifies Financial ledger state and posts the delta.
        """
        if customer is None or customer.business_id != business.id:
            raise ValidationError("A customer belonging to this business is required.")

        expected_settled_amount = Decimal(str(expected_settled_amount))
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValidationError("The order has no positive outstanding settlement amount.")

        settled_amount, _ = WalletService.validated_order_settlement(
            business=business,
            order_id=order_id,
            customer_id=customer.pk,
        )
        if settled_amount != expected_settled_amount:
            raise ValidationError(
                "Order wallet ledger changed after Sales validated the settlement. Retry the operation."
            )

        account = WalletService.get_or_create_account(
            business=business,
            customer=customer,
        )
        account = CustomerAccount.objects.select_for_update().get(pk=account.pk)
        WalletService._validated_balance_history(account)
        account.balance -= amount
        account.save(update_fields=["balance"])
        return CustomerTransaction.objects.create(
            account=account,
            order_id=order_id,
            type=CustomerTransaction.Type.DEBIT,
            amount=amount,
            balance_after=account.balance,
            description=f"Order #{order_id} settlement debit",
            is_order_settlement=True,
            is_order_settlement_verified=True,
        )

    @staticmethod
    def _record_debit(*, account, order_id, amount, description):
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValidationError("Amount must be positive.")
        account.balance -= amount
        account.save(update_fields=["balance"])
        return CustomerTransaction.objects.create(
            account=account,
            order_id=order_id,
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
    def validated_order_settlement(*, business, order_id, customer_id):
        """Validate the Financial ledger for one Sales-owned order reference."""
        if not customer_id:
            transactions = list(
                CustomerTransaction.objects.filter(order_id=order_id).order_by("id")
            )
            return Decimal("0"), transactions

        customer = Customer.objects.filter(pk=customer_id, business=business).first()
        if customer is None:
            raise ValidationError("A customer belonging to this business is required.")

        account = CustomerAccount.objects.select_for_update().filter(
            customer_id=customer_id
        ).first()
        if account and account.business_id != business.id:
            raise ValidationError("Customer account belongs to a different business.")

        account_history = (
            WalletService._validated_balance_history(account) if account else []
        )
        transactions = [
            entry for entry in account_history if entry.order_id == order_id
        ]
        order_entries = CustomerTransaction.objects.filter(order_id=order_id)
        if order_entries.exclude(
            account_id=account.id if account else None
        ).exists():
            raise ValidationError("Order wallet entries belong to another customer account.")
        if not account and order_entries.exists():
            raise ValidationError("Order wallet entries have no customer account.")

        settled_amount = Decimal("0")
        for txn in transactions:
            if (
                not txn.is_order_settlement
                or not txn.is_order_settlement_verified
                or txn.account_id != account.id
                or account.customer_id != customer_id
                or account.business_id != business.id
                or txn.amount <= 0
                or txn.type not in (
                    CustomerTransaction.Type.DEBIT,
                    CustomerTransaction.Type.CREDIT,
                )
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
                    refund.order_id != order_id
                    or refund.business_id != business.id
                    or refund.customer_id != customer_id
                    or refund.payment_method != CUSTOMER_ACCOUNT_PAYMENT_METHOD
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

    @staticmethod
    def _validate_order_reference(business, customer, order):
        if order is not None and (
            order.business_id != business.id or order.customer_id != customer.id
        ):
            raise ValidationError("Order does not belong to this customer and business.")
