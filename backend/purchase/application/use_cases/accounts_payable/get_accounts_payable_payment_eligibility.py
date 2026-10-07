from purchase.application.dto.accounts_payable_payment_eligibility import (
    AccountsPayablePaymentEligibilityResult,
    GetAccountsPayablePaymentEligibilityQuery,
)
from purchase.domain.repositories.accounts_payable_repository import AccountsPayableRepository
from purchase.domain.repositories.payment_allocation_repository import PaymentAllocationRepository
from purchase.domain.services.accounts_payable_payment_state import AccountsPayablePaymentStatePolicy


class GetAccountsPayablePaymentEligibility:
    def __init__(
        self,
        repository: AccountsPayableRepository,
        allocation_repository: PaymentAllocationRepository,
    ) -> None:
        self._repository = repository
        self._allocations = allocation_repository

    def execute(
        self,
        query: GetAccountsPayablePaymentEligibilityQuery,
    ) -> AccountsPayablePaymentEligibilityResult:
        self._positive_id(query.business_id, "Business ID")
        self._positive_id(query.accounts_payable_id, "Accounts payable ID")

        payable = self._repository.get_by_id_for_business(
            query.accounts_payable_id,
            query.business_id,
        )
        if payable is None:
            raise ValueError("Accounts payable does not exist in this business.")

        allocated = self._allocations.allocated_amount_for_accounts_payable(
            query.business_id, payable.id,
        )
        state = AccountsPayablePaymentStatePolicy.calculate(payable, allocated)
        return AccountsPayablePaymentEligibilityResult(
            accounts_payable_id=payable.id,
            eligible=state.eligible,
            status=state.status,
            amount=payable.amount,
            allocated_amount=state.allocated_amount,
            outstanding_amount=state.outstanding_amount,
            reason=state.reason,
        )

    @staticmethod
    def _positive_id(value: int, label: str) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{label} must be a positive integer.")
