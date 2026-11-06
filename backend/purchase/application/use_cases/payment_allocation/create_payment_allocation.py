from uuid import UUID

from purchase.application.dto.payment_allocation import (
    CreatePaymentAllocationCommand,
    PaymentAllocationResult,
)
from purchase.application.exceptions import (
    PaymentAllocationIdempotencyKeyRace,
    PaymentAllocationIdempotencyPayloadMismatch,
)
from purchase.application.ports.goods_receipt import TransactionManager
from purchase.application.use_cases.payment_allocation.canonicalization import (
    CANONICALIZATION_VERSION,
    payment_allocation_payload_fingerprint,
)
from purchase.domain.entities.payment_allocation import PaymentAllocation
from purchase.domain.repositories.accounts_payable_repository import AccountsPayableRepository
from purchase.domain.repositories.payment_allocation_repository import PaymentAllocationRepository
from purchase.domain.repositories.supplier_payment_repository import SupplierPaymentRepository
from purchase.domain.services.accounts_payable_payment_state import AccountsPayablePaymentStatePolicy
from purchase.domain.enums.accounts_payable_status import AccountsPayableStatus


class CreatePaymentAllocation:
    """Atomically allocate payment funds with business-scoped replay protection."""

    def __init__(
        self,
        accounts_payable_repository: AccountsPayableRepository,
        supplier_payment_repository: SupplierPaymentRepository,
        allocation_repository: PaymentAllocationRepository,
        transaction_manager: TransactionManager,
    ) -> None:
        self._payables = accounts_payable_repository
        self._payments = supplier_payment_repository
        self._allocations = allocation_repository
        self._transactions = transaction_manager

    def execute(self, command: CreatePaymentAllocationCommand) -> PaymentAllocationResult:
        self._positive_id(command.business_id, "Business ID")
        self._positive_id(command.accounts_payable_id, "Accounts payable ID")
        self._positive_id(command.supplier_payment_id, "Supplier payment ID")
        if not isinstance(command.idempotency_key, UUID):
            raise ValueError("Idempotency key must be a UUID.")

        normalized = PaymentAllocation(
            id=None,
            business_id=command.business_id,
            accounts_payable_id=command.accounts_payable_id,
            supplier_payment_id=command.supplier_payment_id,
            amount=command.amount,
            allocated_at=command.allocated_at,
        )
        fingerprint = payment_allocation_payload_fingerprint(command)
        allocation = PaymentAllocation(
            id=None,
            business_id=normalized.business_id,
            accounts_payable_id=normalized.accounts_payable_id,
            supplier_payment_id=normalized.supplier_payment_id,
            amount=normalized.amount,
            allocated_at=normalized.allocated_at,
            idempotency_key=command.idempotency_key,
            payload_fingerprint=fingerprint,
            payload_version=CANONICALIZATION_VERSION,
        )

        try:
            with self._transactions.atomic():
                existing = self._allocations.get_by_idempotency_key_for_business(
                    command.idempotency_key,
                    command.business_id,
                )
                if existing is not None:
                    return self._replay_result(existing, fingerprint)

                # Deterministic lock order for every allocation request: AP, then payment.
                if not self._payables.lock_for_payment_allocation(
                    command.business_id, command.accounts_payable_id,
                ):
                    raise ValueError("Accounts payable does not exist in this business.")
                if not self._payments.lock_for_allocation(
                    command.business_id, command.supplier_payment_id,
                ):
                    raise ValueError("Supplier payment does not exist in this business.")

                # A same-key request may have committed while this request
                # waited for either aggregate lock.
                existing = self._allocations.get_by_idempotency_key_for_business(
                    command.idempotency_key,
                    command.business_id,
                )
                if existing is not None:
                    return self._replay_result(existing, fingerprint)

                payable = self._payables.get_by_id_for_business(
                    command.accounts_payable_id, command.business_id,
                )
                payment = self._payments.get_by_id_for_business(
                    command.supplier_payment_id, command.business_id,
                )
                if payable is None:
                    raise ValueError("Accounts payable does not exist in this business.")
                if payment is None:
                    raise ValueError("Supplier payment does not exist in this business.")
                if payable.business_id != payment.business_id:
                    raise ValueError("Accounts payable and supplier payment must belong to the same business.")
                if payable.supplier_id != payment.supplier_id:
                    raise ValueError("Supplier payment supplier does not match accounts payable supplier.")
                if payable.status == AccountsPayableStatus.CANCELLED:
                    raise ValueError("Cannot allocate a payment to a cancelled accounts payable.")

                ap_allocated = self._allocations.allocated_amount_for_accounts_payable(
                    command.business_id, payable.id,
                )
                payment_allocated = self._allocations.allocated_amount_for_supplier_payment(
                    command.business_id, payment.id,
                )
                ap_state = AccountsPayablePaymentStatePolicy.calculate(payable, ap_allocated)
                payment_remaining = payment.amount - payment_allocated
                if ap_state.outstanding_amount <= 0:
                    raise ValueError("Accounts payable is already fully paid.")
                if allocation.amount > ap_state.outstanding_amount:
                    raise ValueError("Allocation amount exceeds accounts payable outstanding amount.")
                if allocation.amount > payment_remaining:
                    raise ValueError("Allocation amount exceeds supplier payment remaining amount.")

                saved = self._allocations.create(allocation)
                updated_allocated = self._allocations.allocated_amount_for_accounts_payable(
                    command.business_id, payable.id,
                )
                updated_state = AccountsPayablePaymentStatePolicy.calculate(
                    payable, updated_allocated,
                )
                self._payables.save_payment_status(
                    payable.id, command.business_id, updated_state.status,
                )
                return PaymentAllocationResult(allocation=saved, replayed=False)
        except PaymentAllocationIdempotencyKeyRace as race:
            # The failed insert savepoint and outer transaction have rolled back
            # before this read, so the committed winner is visible here.
            winner = self._allocations.get_by_idempotency_key_for_business(
                command.idempotency_key,
                command.business_id,
            )
            if winner is None:
                raise race.original_error
            return self._replay_result(winner, fingerprint)

    @staticmethod
    def _replay_result(
        existing: PaymentAllocation,
        fingerprint: str,
    ) -> PaymentAllocationResult:
        if (
            existing.payload_version != CANONICALIZATION_VERSION
            or existing.payload_fingerprint != fingerprint
        ):
            raise PaymentAllocationIdempotencyPayloadMismatch(
                "This idempotency key was already used with different payment allocation data."
            )
        return PaymentAllocationResult(allocation=existing, replayed=True)

    @staticmethod
    def _positive_id(value: int, label: str) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{label} must be a positive integer.")
