from catalog.application.exceptions import ProductNotFound
from catalog.application.ports.product_query_repository import ProductQueryRepository


class GetProduct:
    """Fetch one Catalog product without leaking tenant-scoped ORM queries."""

    def __init__(self, repository: ProductQueryRepository):
        self.repository = repository

    def execute(self, *, business_id: int, product_id: int):
        product = self.repository.get_for_business(
            business_id=business_id,
            product_id=product_id,
        )
        if product is None:
            raise ProductNotFound("Product does not exist in this business.")
        return product
