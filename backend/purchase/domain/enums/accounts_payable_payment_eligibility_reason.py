from enum import StrEnum


class AccountsPayablePaymentEligibilityReason(StrEnum):
    ALREADY_PAID = "already_paid"
    CANCELLED = "cancelled"
