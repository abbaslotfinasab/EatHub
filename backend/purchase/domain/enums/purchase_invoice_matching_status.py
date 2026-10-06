from enum import StrEnum


class PurchaseInvoiceMatchingStatus(StrEnum):
    NOT_MATCHED = "not_matched"
    PENDING_RECEIPT = "pending_receipt"
    MATCHED = "matched"
    EXCEPTION = "exception"
