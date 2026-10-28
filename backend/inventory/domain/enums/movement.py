from enum import StrEnum


class MovementDirection(StrEnum):
    IN = "in"
    OUT = "out"


class MovementType(StrEnum):
    RECEIPT = "receipt"
    ISSUE = "issue"
    TRANSFER_DISPATCH = "transfer_dispatch"
    TRANSFER_RECEIPT = "transfer_receipt"
    ADJUSTMENT = "adjustment"
    REVERSAL = "reversal"
    OPENING_BALANCE = "opening_balance"
