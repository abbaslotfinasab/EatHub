# purchase/domain/enums/payment_method.py

from enum import StrEnum


class PaymentMethod(StrEnum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CARD = "card"
    CHEQUE = "cheque"
    CREDIT = "credit"
    OTHER = "other"