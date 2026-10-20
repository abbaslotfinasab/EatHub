from enum import StrEnum


class MovementDirection(StrEnum):
    IN = "in"
    OUT = "out"


class MovementType(StrEnum):
    RECEIPT = "receipt"
    ADJUSTMENT = "adjustment"
    REVERSAL = "reversal"
