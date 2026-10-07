from abc import ABC, abstractmethod
from decimal import Decimal

from purchase.domain.entities.payment_allocation import PaymentAllocation


class PaymentAllocationRepository(ABC):
    @abstractmethod
    def create(self, allocation: PaymentAllocation) -> PaymentAllocation:
        raise NotImplementedError

    @abstractmethod
    def get_by_id_for_business(
        self, allocation_id: int, business_id: int
    ) -> PaymentAllocation | None:
        raise NotImplementedError

    @abstractmethod
    def list(
        self,
        business_id: int,
        *,
        accounts_payable_id: int | None = None,
        supplier_payment_id: int | None = None,
    ) -> list[PaymentAllocation]:
        raise NotImplementedError

    @abstractmethod
    def allocated_amount_for_accounts_payable(
        self, business_id: int, accounts_payable_id: int
    ) -> Decimal:
        raise NotImplementedError

    @abstractmethod
    def allocated_amount_for_supplier_payment(
        self, business_id: int, supplier_payment_id: int
    ) -> Decimal:
        raise NotImplementedError
