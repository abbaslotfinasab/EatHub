from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from purchase.domain.entities.accounts_payable import AccountsPayable, MONEY_QUANTUM
from purchase.domain.enums.accounts_payable_payment_eligibility_reason import (
    AccountsPayablePaymentEligibilityReason,
)
from purchase.domain.enums.accounts_payable_status import AccountsPayableStatus


@dataclass(frozen=True)
class AccountsPayablePaymentState:
    allocated_amount: Decimal
    outstanding_amount: Decimal
    status: AccountsPayableStatus
    eligible: bool
    reason: AccountsPayablePaymentEligibilityReason | None


class AccountsPayablePaymentStatePolicy:
    @staticmethod
    def eligibility_for_status(status: AccountsPayableStatus):
        if status in (AccountsPayableStatus.OPEN, AccountsPayableStatus.PARTIALLY_PAID):
            return True, None
        if status == AccountsPayableStatus.PAID:
            return False, AccountsPayablePaymentEligibilityReason.ALREADY_PAID
        return False, AccountsPayablePaymentEligibilityReason.CANCELLED

    @staticmethod
    def calculate(
        payable: AccountsPayable,
        allocated_amount: Decimal,
    ) -> AccountsPayablePaymentState:
        if not isinstance(allocated_amount, Decimal):
            raise ValueError("Allocated amount must be a Decimal.")
        allocated = allocated_amount.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)
        if allocated < 0 or allocated > payable.amount:
            raise ValueError("Allocated amount must be between zero and the payable amount.")

        outstanding = (payable.amount - allocated).quantize(MONEY_QUANTUM)
        if payable.status == AccountsPayableStatus.CANCELLED:
            status = AccountsPayableStatus.CANCELLED
        else:
            if allocated == 0:
                status = AccountsPayableStatus.OPEN
            elif allocated < payable.amount:
                status = AccountsPayableStatus.PARTIALLY_PAID
            else:
                status = AccountsPayableStatus.PAID
        eligible, reason = AccountsPayablePaymentStatePolicy.eligibility_for_status(status)

        return AccountsPayablePaymentState(
            allocated_amount=allocated,
            outstanding_amount=outstanding,
            status=status,
            eligible=eligible,
            reason=reason,
        )
