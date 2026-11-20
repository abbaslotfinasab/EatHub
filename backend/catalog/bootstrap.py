from catalog.application.use_cases.get_product_read_model import GetProductReadModel
from catalog.infrastructure.django.product_read_repository import DjangoProductReadRepository


def get_product_read_model(*, business_id: int, product_id: int) -> dict:
    """Composition entry point for the Catalog product read use case."""
    return GetProductReadModel(DjangoProductReadRepository()).execute(
        business_id=business_id,
        product_id=product_id,
    )
