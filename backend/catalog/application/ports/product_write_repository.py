from typing import Protocol


class ProductWriteRepository(Protocol):
    """Persistence port for business-scoped Catalog product writes."""

    def create(self, *, business_id: int, data: dict): ...

    def update(self, *, business_id: int, product_id: int, data: dict): ...
