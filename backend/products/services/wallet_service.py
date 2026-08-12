from decimal import Decimal

from django.db import transaction

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

        account, _ = CustomerAccount.objects.get_or_create(
            business=business,
            customer=customer,
        )

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

        account = WalletService.get_or_create_account(
            business=business,
            customer=customer,
        )

        account = (
            CustomerAccount.objects
            .select_for_update()
            .get(pk=account.pk)
        )

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

        account = WalletService.get_or_create_account(
            business=business,
            customer=customer,
        )

        account = (
            CustomerAccount.objects
            .select_for_update()
            .get(pk=account.pk)
        )

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