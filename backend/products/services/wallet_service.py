from decimal import Decimal

from django.db import transaction

from products.models import CustomerTransaction, CustomerAccount, Customer, Order


class WalletService:

    @staticmethod
    def get_account(
            *,
            business,
            customer: Customer,
    ) -> CustomerAccount | None:
        return CustomerAccount.objects.filter(
            business=business,
            customer=customer,
        ).first()

    @staticmethod
    @transaction.atomic
    def credit(
            *,
            account: CustomerAccount,
            amount: Decimal,
            description: str = "",
            order: Order | None = None,
    ) -> CustomerTransaction:
        """
        شارژ حساب مشتری
        """

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
            account: CustomerAccount,
            amount: Decimal,
            description: str = "",
            order: Order | None = None,
    ) -> CustomerTransaction:
        """
        کسر از حساب مشتری
        اجازه منفی شدن موجودی وجود دارد.
        """

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
            account: CustomerAccount,
            amount: Decimal,
            description: str = "",
    ) -> CustomerTransaction:
        """
        اصلاح دستی موجودی.
        amount می‌تواند مثبت یا منفی باشد.
        """

        account.balance += amount
        account.save(update_fields=["balance"])

        return CustomerTransaction.objects.create(
            account=account,
            type=CustomerTransaction.Type.ADJUST,
            amount=amount,
            description=description,
        )

    @staticmethod
    def get_balance(*, account: CustomerAccount) -> Decimal:
        return account.balance
