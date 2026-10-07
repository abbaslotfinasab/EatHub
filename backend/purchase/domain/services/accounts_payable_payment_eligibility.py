from dataclasses import dataclass

from purchase.domain.entities.accounts_payable import AccountsPayable
from purchase.domain.enums.accounts_payable_payment_eligibility_reason import (
    AccountsPayablePaymentEligibilityReason,
)
from purchase.domain.enums.accounts_payable_status import AccountsPayableStatus
from purchase.domain.services.accounts_payable_payment_state import AccountsPayablePaymentStatePolicy


@dataclass(frozen=True)
class AccountsPayablePaymentEligibility:
    eligible: bool
    reason: AccountsPayablePaymentEligibilityReason | None = None


class AccountsPayablePaymentEligibilityPolicy:
    @staticmethod
    def evaluate(
        accounts_payable: AccountsPayable,
    ) -> AccountsPayablePaymentEligibility:
        eligible, reason = AccountsPayablePaymentStatePolicy.eligibility_for_status(
            accounts_payable.status,
        )
        return AccountsPayablePaymentEligibility(
            eligible=eligible,
            reason=reason,
        )
