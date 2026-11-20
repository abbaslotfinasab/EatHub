from catalog.application.exceptions import ProductsUnavailable
from catalog.application.ports.product_read_repository import ProductReadRepository


class ResolveActiveProducts:
    """Resolve active Catalog products without exposing persistence to consumers."""

    def __init__(self, repository: ProductReadRepository):
        self.repository = repository

    def execute(self, *, business_id: int, product_ids: set[int]) -> dict:
        ids = set(product_ids)
        if not ids:
            return {}

        products = self.repository.get_active_products_for_business(
            business_id=business_id,
            product_ids=ids,
        )
        if ids != set(products):
            raise ProductsUnavailable
        return products
