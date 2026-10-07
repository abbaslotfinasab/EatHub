from django.db import IntegrityError, transaction

from purchase.domain.entities.accounts_payable import AccountsPayable
from purchase.domain.enums.accounts_payable_status import AccountsPayableStatus
from purchase.domain.repositories.accounts_payable_repository import AccountsPayableRepository
from purchase.infrastructure.persistence.django.mappers import AccountsPayableMapper
from purchase.models import (
    AccountsPayable as DjangoAccountsPayable,
    PurchaseInvoice as DjangoPurchaseInvoice,
    Supplier as DjangoSupplier,
)


class DjangoAccountsPayableRepository(AccountsPayableRepository):
    def lock_for_payment_allocation(self, business_id: int, accounts_payable_id: int) -> bool:
        return DjangoAccountsPayable.objects.select_for_update(of=("self",)).filter(
            id=accounts_payable_id,
            business_id=business_id,
        ).exists()

    def create(self, accounts_payable: AccountsPayable) -> AccountsPayable:
        accounts_payable.validate()
        if accounts_payable.id is not None:
            raise ValueError("Accounts payable repository create requires a new aggregate.")

        source_invoice = DjangoPurchaseInvoice.objects.filter(
            id=accounts_payable.source_invoice_id,
            business_id=accounts_payable.business_id,
        ).values("business_id", "supplier_id").first()
        if source_invoice is None:
            raise ValueError("Purchase invoice does not exist in this business.")
        if source_invoice["supplier_id"] != accounts_payable.supplier_id:
            raise ValueError("Accounts payable supplier does not match its source invoice.")
        if not DjangoSupplier.objects.filter(
            id=accounts_payable.supplier_id,
            business_id=accounts_payable.business_id,
        ).exists():
            raise ValueError("Supplier does not exist in this business.")

        model = AccountsPayableMapper.to_model(accounts_payable)
        try:
            # Keep a savepoint so a uniqueness violation does not poison the caller's transaction.
            with transaction.atomic():
                model.save(force_insert=True)
        except IntegrityError as error:
            if self.exists_for_source_invoice(
                accounts_payable.source_invoice_id,
                accounts_payable.business_id,
            ):
                raise ValueError("Accounts payable already exists for this purchase invoice.") from error
            raise
        return AccountsPayableMapper.to_domain(model)

    def get_by_id_for_business(
        self, accounts_payable_id: int, business_id: int
    ) -> AccountsPayable | None:
        model = DjangoAccountsPayable.objects.filter(
            id=accounts_payable_id,
            business_id=business_id,
        ).first()
        return None if model is None else AccountsPayableMapper.to_domain(model)

    def get_by_source_invoice_id(
        self, source_invoice_id: int, business_id: int
    ) -> AccountsPayable | None:
        model = DjangoAccountsPayable.objects.filter(
            source_invoice_id=source_invoice_id,
            business_id=business_id,
        ).first()
        return None if model is None else AccountsPayableMapper.to_domain(model)

    def list(self, business_id: int) -> list[AccountsPayable]:
        return [
            AccountsPayableMapper.to_domain(model)
            for model in DjangoAccountsPayable.objects.filter(
                business_id=business_id,
            ).order_by("id")
        ]

    def exists_for_source_invoice(self, source_invoice_id: int, business_id: int) -> bool:
        return DjangoAccountsPayable.objects.filter(
            source_invoice_id=source_invoice_id,
            business_id=business_id,
        ).exists()

    def save_payment_status(
        self,
        accounts_payable_id: int,
        business_id: int,
        status: AccountsPayableStatus,
    ) -> None:
        if status == AccountsPayableStatus.CANCELLED:
            raise ValueError("Payment allocations cannot change cancelled accounts payable status.")
        model = DjangoAccountsPayable.objects.filter(
            id=accounts_payable_id,
            business_id=business_id,
        ).exclude(status=AccountsPayableStatus.CANCELLED.value).first()
        if model is None:
            raise ValueError("Accounts payable does not exist in this business.")
        model.status = status.value
        model.save(update_fields=["status", "updated_at"])
