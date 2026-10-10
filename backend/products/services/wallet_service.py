from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from products.models import (
    Customer,
    CustomerAccount,
    CustomerTransaction,
    Order,
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
            defaults={"business": business},
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
    ) -> CustomerTransaction:

        WalletService._validate_order_reference(business, customer, order)

        account = WalletService.get_or_create_account(
            business=business,
            customer=customer,
        )

        account = (
            CustomerAccount.objects
            .select_for_update()
            .get(pk=account.pk)
        )

        amount = Decimal(amount)
        if amount <= 0:
            raise ValidationError("Amount must be positive.")
        account.balance += amount

        account.save(
            update_fields=["balance"]
        )

        return CustomerTransaction.objects.create(
            account=account,
            order=order,
            type=CustomerTransaction.Type.CREDIT,
            amount=amount,
            balance_after=account.balance,
            description=description,
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
        if order is not None and CustomerTransaction.objects.filter(
            order=order,
            type=CustomerTransaction.Type.DEBIT,
        ).exists():
            raise ValidationError("Order already has a wallet debit.")

        account = WalletService.get_or_create_account(
            business=business,
            customer=customer,
        )

        account = (
            CustomerAccount.objects
            .select_for_update()
            .get(pk=account.pk)
        )

        amount = Decimal(amount)
        if amount <= 0:
            raise ValidationError("Amount must be positive.")
        account.balance -= amount

        account.save(
            update_fields=["balance"]
        )

        return CustomerTransaction.objects.create(
            account=account,
            order=order,
            type=CustomerTransaction.Type.DEBIT,
            amount=amount,
            balance_after=account.balance,
            description=description,
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
    def _validate_order_reference(business, customer, order):
        if order is not None and (
            order.business_id != business.id or order.customer_id != customer.id
        ):
            raise ValidationError("Order does not belong to this customer and business.")
