from catalog.application.exceptions import ProductNotFound
from catalog.application.ports.product_write_repository import ProductWriteRepository


class UpdateProduct:
    """Update a product without allowing it to cross business boundaries."""

    def __init__(self, repository: ProductWriteRepository):
        self.repository = repository

    def execute(self, *, business_id: int, product_id: int, data: dict):
        product = self.repository.update(
            business_id=business_id,
            product_id=product_id,
            data=dict(data),
        )
        if product is None:
            raise ProductNotFound("Product does not exist in this business.")
        return product
