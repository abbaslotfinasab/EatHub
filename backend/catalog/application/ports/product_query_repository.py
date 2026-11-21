from typing import Any, Protocol


class ProductQueryRepository(Protocol):
    """Read port for business-scoped Catalog Product API queries."""

    def list_for_business(
        self, *, business_id: int, search: str | None, category: str | None,
        status: str | None, page: int, page_size: int,
    ) -> tuple[int, list[Any]]:
        """Return total count and one ordered page of products."""

    def get_for_business(self, *, business_id: int, product_id: int) -> Any | None:
        """Return a product with read relations, or None outside the business."""
