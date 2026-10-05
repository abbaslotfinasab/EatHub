from purchase.application.dto.supplier_payment import ListSupplierPaymentsQuery
from purchase.domain.entities.supplier_payment import SupplierPayment
from purchase.domain.repositories.supplier_payment_repository import (
    SupplierPaymentRepository,
)


class ListSupplierPaymentsUseCase:
    def __init__(self, payment_repository: SupplierPaymentRepository) -> None:
        self._payment_repository = payment_repository

    def execute(self, query: ListSupplierPaymentsQuery) -> list[SupplierPayment]:
        if not isinstance(query.business_id, int) or query.business_id <= 0:
            raise ValueError("Business ID must be a positive integer.")
        if query.supplier_id is not None and (
            not isinstance(query.supplier_id, int) or query.supplier_id <= 0
        ):
            raise ValueError("Supplier ID must be a positive integer.")
        return self._payment_repository.list(
            query.business_id,
            supplier_id=query.supplier_id,
            method=query.method,
            payment_date_from=query.payment_date_from,
            payment_date_to=query.payment_date_to,
        )
