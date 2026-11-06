from uuid import UUID

from purchase.application.dto.supplier_payment import CreateSupplierPaymentDTO
from purchase.application.exceptions import (
    SupplierPaymentIdempotencyKeyRace,
    SupplierPaymentIdempotencyPayloadMismatch,
)
from purchase.application.use_cases.supplier_payment.canonicalization import (
    CANONICALIZATION_VERSION,
    supplier_payment_payload_fingerprint,
)
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

    def execute(self, command: CreateSupplierPaymentDTO) -> tuple[SupplierPayment, bool]:
        business_id = self._validate_positive_id(command.business_id, "Business ID")
        supplier_id = self._validate_positive_id(command.supplier_id, "Supplier ID")
        if not isinstance(command.idempotency_key, UUID):
            raise ValueError("Idempotency key must be a UUID.")

        fingerprint = supplier_payment_payload_fingerprint(command)
        existing = self._payment_repository.get_by_idempotency_key_for_business(
            command.idempotency_key,
            business_id,
        )
        if existing is not None:
            return self._replay(existing, fingerprint), True

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
            idempotency_key=command.idempotency_key,
            payload_fingerprint=fingerprint,
            payload_version=CANONICALIZATION_VERSION,
        )
        try:
            return self._payment_repository.save(payment), False
        except SupplierPaymentIdempotencyKeyRace as race:
            winner = self._payment_repository.get_by_idempotency_key_for_business(
                command.idempotency_key,
                business_id,
            )
            if winner is None:
                raise race.original_error
            return self._replay(winner, fingerprint), True

    @staticmethod
    def _replay(existing: SupplierPayment, fingerprint: str) -> SupplierPayment:
        if (
            existing.payload_version != CANONICALIZATION_VERSION
            or existing.payload_fingerprint != fingerprint
        ):
            raise SupplierPaymentIdempotencyPayloadMismatch(
                "This idempotency key was already used with different supplier payment data."
            )
        return existing

    @staticmethod
    def _validate_positive_id(value: int, field_name: str) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")
        return value
