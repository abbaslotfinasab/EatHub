from enum import StrEnum


class PurchaseInvoiceMatchException(StrEnum):
    RECEIPT_PENDING = "RECEIPT_PENDING"
    INVOICE_OVER_RECEIVED = "INVOICE_OVER_RECEIVED"
    PRICE_VARIANCE = "PRICE_VARIANCE"
