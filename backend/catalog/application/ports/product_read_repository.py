from typing import Protocol


class ProductReadRepository(Protocol):
    """Persistence port for Catalog product read models."""

    def get_read_model_for_business(self, *, business_id: int, product_id: int) -> dict:
        """Return a product read model or None when it is outside the business."""
