from purchase.domain.entities.supplier_payment import SupplierPayment
from purchase.domain.repositories.supplier_payment_repository import (
    SupplierPaymentRepository,
)


class GetSupplierPaymentUseCase:
    def __init__(self, payment_repository: SupplierPaymentRepository) -> None:
        self._payment_repository = payment_repository

    def execute(self, payment_id: int, business_id: int) -> SupplierPayment:
        if not isinstance(payment_id, int) or payment_id <= 0:
            raise ValueError("Supplier payment ID must be a positive integer.")
        if not isinstance(business_id, int) or business_id <= 0:
            raise ValueError("Business ID must be a positive integer.")
        payment = self._payment_repository.get_by_id_for_business(
            payment_id,
            business_id,
        )
        if payment is None:
            raise ValueError("Supplier payment does not exist in this business.")
        return payment
