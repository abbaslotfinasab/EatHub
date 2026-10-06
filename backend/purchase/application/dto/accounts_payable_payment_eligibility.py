from dataclasses import dataclass
from decimal import Decimal

from purchase.domain.enums.accounts_payable_payment_eligibility_reason import (
    AccountsPayablePaymentEligibilityReason,
)
from purchase.domain.enums.accounts_payable_status import AccountsPayableStatus


@dataclass(frozen=True)
class GetAccountsPayablePaymentEligibilityQuery:
    business_id: int
    accounts_payable_id: int


@dataclass(frozen=True)
class AccountsPayablePaymentEligibilityResult:
    accounts_payable_id: int
    eligible: bool
    status: AccountsPayableStatus
    amount: Decimal
    reason: AccountsPayablePaymentEligibilityReason | None
