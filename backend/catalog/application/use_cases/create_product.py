from catalog.application.ports.product_write_repository import ProductWriteRepository


class CreateProduct:
    """Create a product through the Catalog write persistence port."""

    def __init__(self, repository: ProductWriteRepository):
        self.repository = repository

    def execute(self, *, business_id: int, data: dict):
        return self.repository.create(business_id=business_id, data=dict(data))
