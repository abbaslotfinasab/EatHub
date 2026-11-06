class PurchaseInventoryIntegrationError(ValueError):
    """An expected Inventory business failure prevented a Purchase receipt."""


class GoodsReceiptIdempotencyPayloadMismatch(Exception):
    """An idempotency key was already used for different receipt data."""


class GoodsReceiptIdempotencyKeyRace(Exception):
    """A concurrent receipt insert claimed the idempotency key first."""

    def __init__(self, original_error: Exception) -> None:
        super().__init__("A goods receipt idempotency key was claimed concurrently.")
        self.original_error = original_error


class PaymentAllocationIdempotencyPayloadMismatch(ValueError):
    """An allocation idempotency key was reused for different financial data."""


class PaymentAllocationIdempotencyKeyRace(Exception):
    """A concurrent allocation insert claimed the idempotency key first."""

    def __init__(self, original_error: Exception) -> None:
        super().__init__("A payment allocation idempotency key was claimed concurrently.")
        self.original_error = original_error


class SupplierPaymentIdempotencyPayloadMismatch(ValueError):
    """A supplier payment key was reused for different financial data."""


class SupplierPaymentIdempotencyKeyRace(Exception):
    """A concurrent supplier payment insert claimed the key first."""

    def __init__(self, original_error: Exception) -> None:
        super().__init__("A supplier payment idempotency key was claimed concurrently.")
        self.original_error = original_error
