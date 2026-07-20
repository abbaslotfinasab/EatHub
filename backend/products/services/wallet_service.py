from decimal import Decimal

from django.db import transaction

from products.models import CustomerTransaction, CustomerAccount, Customer, Order


class WalletService:

    @staticmethod
    @transaction.atomic
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
        """
        شارژ حساب مشتری
        """

        account = WalletService.get_or_create_account(
            business=business,
            customer=customer,
        )

        account.balance += amount
        account.save(update_fields=["balance"])

        return CustomerTransaction.objects.create(
            account=account,
            order=order,
            type=CustomerTransaction.Type.CREDIT,
            amount=amount,
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
        """
        کسر از حساب مشتری
        اجازه منفی شدن موجودی وجود دارد.
        """

        account = WalletService.get_or_create_account(
            business=business,
            customer=customer,
        )

        account.balance -= amount
        account.save(update_fields=["balance"])

        return CustomerTransaction.objects.create(
            account=account,
            order=order,
            type=CustomerTransaction.Type.DEBIT,
            amount=amount,
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
        """
        اصلاح دستی موجودی.
        amount می‌تواند مثبت یا منفی باشد.
        """

        account = WalletService.get_or_create_account(
            business=business,
            customer=customer,
        )

        account.balance = amount
        account.save(update_fields=["balance"])

        return CustomerTransaction.objects.create(
            account=account,
            type=CustomerTransaction.Type.ADJUST,
            amount=amount,
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
