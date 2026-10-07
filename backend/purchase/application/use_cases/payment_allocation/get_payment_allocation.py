from purchase.domain.repositories.payment_allocation_repository import PaymentAllocationRepository


class GetPaymentAllocation:
    def __init__(self, repository: PaymentAllocationRepository) -> None:
        self._repository = repository

    def execute(self, allocation_id: int, business_id: int):
        if not isinstance(business_id, int) or business_id <= 0:
            raise ValueError("Business ID must be a positive integer.")
        if not isinstance(allocation_id, int) or allocation_id <= 0:
            raise ValueError("Payment allocation ID must be a positive integer.")
        allocation = self._repository.get_by_id_for_business(allocation_id, business_id)
        if allocation is None:
            raise ValueError("Payment allocation does not exist in this business.")
        return allocation
