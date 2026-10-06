from purchase.application.dto.accounts_payable_payment_eligibility import (
    AccountsPayablePaymentEligibilityResult,
    GetAccountsPayablePaymentEligibilityQuery,
)
from purchase.domain.repositories.accounts_payable_repository import AccountsPayableRepository
from purchase.domain.services.accounts_payable_payment_eligibility import (
    AccountsPayablePaymentEligibilityPolicy,
)


class GetAccountsPayablePaymentEligibility:
    def __init__(self, repository: AccountsPayableRepository) -> None:
        self._repository = repository

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

        decision = AccountsPayablePaymentEligibilityPolicy.evaluate(payable)
        return AccountsPayablePaymentEligibilityResult(
            accounts_payable_id=payable.id,
            eligible=decision.eligible,
            status=payable.status,
            amount=payable.amount,
            reason=decision.reason,
        )

    @staticmethod
    def _positive_id(value: int, label: str) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{label} must be a positive integer.")
