from dataclasses import dataclass

from purchase.domain.entities.accounts_payable import AccountsPayable
from purchase.domain.enums.accounts_payable_payment_eligibility_reason import (
    AccountsPayablePaymentEligibilityReason,
)
from purchase.domain.enums.accounts_payable_status import AccountsPayableStatus


@dataclass(frozen=True)
class AccountsPayablePaymentEligibility:
    eligible: bool
    reason: AccountsPayablePaymentEligibilityReason | None = None


class AccountsPayablePaymentEligibilityPolicy:
    @staticmethod
    def evaluate(
        accounts_payable: AccountsPayable,
    ) -> AccountsPayablePaymentEligibility:
        if accounts_payable.status in (
            AccountsPayableStatus.OPEN,
            AccountsPayableStatus.PARTIALLY_PAID,
        ):
            return AccountsPayablePaymentEligibility(eligible=True)
        if accounts_payable.status == AccountsPayableStatus.PAID:
            return AccountsPayablePaymentEligibility(
                eligible=False,
                reason=AccountsPayablePaymentEligibilityReason.ALREADY_PAID,
            )
        return AccountsPayablePaymentEligibility(
            eligible=False,
            reason=AccountsPayablePaymentEligibilityReason.CANCELLED,
        )
