from catalog.application.ports.product_query_repository import ProductQueryRepository


class ListProducts:
    """List Catalog products with business scope and validated query options."""

    def __init__(self, repository: ProductQueryRepository):
        self.repository = repository

    def execute(
        self, *, business_id: int, page: int = 1, page_size: int = 20,
        search: str | None = None, category: str | None = None,
        status: str | None = None,
    ) -> dict:
        count, products = self.repository.list_for_business(
            business_id=business_id,
            search=search,
            category=category,
            status=status,
            page=page,
            page_size=page_size,
        )
        return {
            "count": count,
            "page": page,
            "page_size": page_size,
            "results": products,
        }
