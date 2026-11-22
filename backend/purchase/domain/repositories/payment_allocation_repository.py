from abc import ABC, abstractmethod
from decimal import Decimal
from uuid import UUID

from purchase.domain.entities.payment_allocation import PaymentAllocation


class PaymentAllocationRepository(ABC):
    @abstractmethod
    def create(self, allocation: PaymentAllocation) -> PaymentAllocation:
        raise NotImplementedError

    @abstractmethod
    def get_by_idempotency_key_for_business(
        self, idempotency_key: UUID, business_id: int
    ) -> PaymentAllocation | None:
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

    def allocated_amounts_for_supplier_payments(
        self, business_id: int, supplier_payment_ids: list[int]
    ) -> dict[int, Decimal]:
        """Return allocation totals keyed by supplier payment ID.

        Implementations may override this fallback with a grouped query.
        """
        return {
            payment_id: self.allocated_amount_for_supplier_payment(
                business_id, payment_id
            )
            for payment_id in supplier_payment_ids
        }
