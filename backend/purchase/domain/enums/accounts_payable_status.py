from enum import StrEnum


class AccountsPayableStatus(StrEnum):
    OPEN = "open"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    CANCELLED = "cancelled"
