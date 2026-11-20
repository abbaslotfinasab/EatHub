from catalog.application.ports.product_read_repository import ProductReadRepository


class ProductNotFound(Exception):
    """A Product does not exist inside the requested business."""


class GetProductReadModel:
    """Fetch the Catalog-owned product projection through an application port."""

    def __init__(self, repository: ProductReadRepository):
        self.repository = repository

    def execute(self, *, business_id: int, product_id: int) -> dict:
        product = self.repository.get_read_model_for_business(
            business_id=business_id,
            product_id=product_id,
        )
        if product is None:
            raise ProductNotFound("Product does not exist in this business.")
        return product
