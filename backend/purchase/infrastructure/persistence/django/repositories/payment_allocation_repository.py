from decimal import Decimal

from django.db.models import Sum

from purchase.domain.entities.payment_allocation import PaymentAllocation
from purchase.domain.repositories.payment_allocation_repository import PaymentAllocationRepository
from purchase.infrastructure.persistence.django.mappers import PaymentAllocationMapper
from purchase.models import (
    AccountsPayable as DjangoAccountsPayable,
    PaymentAllocation as DjangoPaymentAllocation,
    SupplierPayment as DjangoSupplierPayment,
)


class DjangoPaymentAllocationRepository(PaymentAllocationRepository):
    def create(self, allocation: PaymentAllocation) -> PaymentAllocation:
        allocation.validate()
        if allocation.id is not None:
            raise ValueError("Payment allocation repository create requires a new event.")

        payable = DjangoAccountsPayable.objects.filter(
            id=allocation.accounts_payable_id,
            business_id=allocation.business_id,
        ).values("supplier_id", "source_invoice_id").first()
        if payable is None:
            raise ValueError("Accounts payable does not exist in this business.")
        payment = DjangoSupplierPayment.objects.filter(
            id=allocation.supplier_payment_id,
            business_id=allocation.business_id,
        ).values("supplier_id").first()
        if payment is None:
            raise ValueError("Supplier payment does not exist in this business.")
        if payable["supplier_id"] != payment["supplier_id"]:
            raise ValueError("Supplier payment supplier does not match accounts payable supplier.")

        model = PaymentAllocationMapper.to_model(allocation)
        model.invoice_id = payable["source_invoice_id"]
        model.save(force_insert=True)
        return PaymentAllocationMapper.to_domain(model)

    def get_by_id_for_business(
        self, allocation_id: int, business_id: int
    ) -> PaymentAllocation | None:
        model = DjangoPaymentAllocation.objects.filter(
            id=allocation_id,
            business_id=business_id,
        ).first()
        return None if model is None else PaymentAllocationMapper.to_domain(model)

    def list(
        self,
        business_id: int,
        *,
        accounts_payable_id: int | None = None,
        supplier_payment_id: int | None = None,
    ) -> list[PaymentAllocation]:
        queryset = DjangoPaymentAllocation.objects.filter(business_id=business_id)
        if accounts_payable_id is not None:
            queryset = queryset.filter(accounts_payable_id=accounts_payable_id)
        if supplier_payment_id is not None:
            queryset = queryset.filter(payment_id=supplier_payment_id)
        return [
            PaymentAllocationMapper.to_domain(model)
            for model in queryset.order_by("id")
        ]

    def allocated_amount_for_accounts_payable(
        self, business_id: int, accounts_payable_id: int
    ) -> Decimal:
        result = DjangoPaymentAllocation.objects.filter(
            business_id=business_id,
            accounts_payable_id=accounts_payable_id,
        ).aggregate(total=Sum("amount"))
        return result["total"] or Decimal("0.00")

    def allocated_amount_for_supplier_payment(
        self, business_id: int, supplier_payment_id: int
    ) -> Decimal:
        result = DjangoPaymentAllocation.objects.filter(
            business_id=business_id,
            payment_id=supplier_payment_id,
        ).aggregate(total=Sum("amount"))
        return result["total"] or Decimal("0.00")
