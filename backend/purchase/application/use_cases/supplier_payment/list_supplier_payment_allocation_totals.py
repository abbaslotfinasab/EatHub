from decimal import Decimal

from purchase.application.dto.supplier_payment_allocation import (
    ListSupplierPaymentAllocationTotalsQuery,
)
from purchase.domain.repositories.payment_allocation_repository import (
    PaymentAllocationRepository,
)


class ListSupplierPaymentAllocationTotalsUseCase:
    def __init__(self, allocation_repository: PaymentAllocationRepository) -> None:
        self._allocation_repository = allocation_repository

    def execute(
        self, query: ListSupplierPaymentAllocationTotalsQuery
    ) -> dict[int, Decimal]:
        if not isinstance(query.business_id, int) or query.business_id <= 0:
            raise ValueError("Business ID must be a positive integer.")
        if any(
            not isinstance(payment_id, int) or payment_id <= 0
            for payment_id in query.supplier_payment_ids
        ):
            raise ValueError("Supplier payment IDs must be positive integers.")

        payment_ids = list(dict.fromkeys(query.supplier_payment_ids))
        if not payment_ids:
            return {}
        return self._allocation_repository.allocated_amounts_for_supplier_payments(
            query.business_id, payment_ids
        )
