class ProductNotFound(Exception):
    """A Product does not exist inside the requested business."""


class ProductSkuConflict(Exception):
    """A SKU is already used by another product in the same business."""
