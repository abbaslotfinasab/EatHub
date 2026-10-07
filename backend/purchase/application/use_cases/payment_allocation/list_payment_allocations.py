from purchase.application.dto.payment_allocation import ListPaymentAllocationsQuery
from purchase.domain.repositories.payment_allocation_repository import PaymentAllocationRepository


class ListPaymentAllocations:
    def __init__(self, repository: PaymentAllocationRepository) -> None:
        self._repository = repository

    def execute(self, query: ListPaymentAllocationsQuery):
        if not isinstance(query.business_id, int) or query.business_id <= 0:
            raise ValueError("Business ID must be a positive integer.")
        for value, label in (
            (query.accounts_payable_id, "Accounts payable ID"),
            (query.supplier_payment_id, "Supplier payment ID"),
        ):
            if value is not None and (not isinstance(value, int) or value <= 0):
                raise ValueError(f"{label} must be a positive integer.")
        return self._repository.list(
            query.business_id,
            accounts_payable_id=query.accounts_payable_id,
            supplier_payment_id=query.supplier_payment_id,
        )
