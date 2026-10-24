class PurchaseInventoryIntegrationError(ValueError):
    """An expected Inventory business failure prevented a Purchase receipt."""


class GoodsReceiptIdempotencyPayloadMismatch(Exception):
    """An idempotency key was already used for different receipt data."""


class GoodsReceiptIdempotencyKeyRace(Exception):
    """A concurrent receipt insert claimed the idempotency key first."""

    def __init__(self, original_error: Exception) -> None:
        super().__init__("A goods receipt idempotency key was claimed concurrently.")
        self.original_error = original_error
