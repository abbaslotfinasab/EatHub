from purchase.application.dto.supplier_payment import CreateSupplierPaymentDTO
from purchase.domain.entities.supplier_payment import SupplierPayment
from purchase.domain.repositories.supplier_payment_repository import (
    SupplierPaymentRepository,
)
from purchase.domain.repositories.supplier_repository import SupplierRepository


class CreateSupplierPaymentUseCase:
    def __init__(
        self,
        payment_repository: SupplierPaymentRepository,
        supplier_repository: SupplierRepository,
    ) -> None:
        self._payment_repository = payment_repository
        self._supplier_repository = supplier_repository

    def execute(self, command: CreateSupplierPaymentDTO) -> SupplierPayment:
        business_id = self._validate_positive_id(command.business_id, "Business ID")
        supplier_id = self._validate_positive_id(command.supplier_id, "Supplier ID")

        supplier = self._supplier_repository.get_by_id_for_business(
            supplier_id,
            business_id,
        )
        if supplier is None:
            raise ValueError("Supplier does not exist in this business.")

        payment = SupplierPayment(
            id=None,
            business_id=business_id,
            supplier_id=supplier_id,
            amount=command.amount,
            payment_date=command.payment_date,
            method=command.method,
        )
        return self._payment_repository.save(payment)

    @staticmethod
    def _validate_positive_id(value: int, field_name: str) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")
        return value
