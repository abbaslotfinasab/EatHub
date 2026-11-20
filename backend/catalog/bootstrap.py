from catalog.application.use_cases.create_product import CreateProduct
from catalog.application.use_cases.get_product_read_model import GetProductReadModel
from catalog.application.use_cases.update_product import UpdateProduct
from catalog.infrastructure.django.product_read_repository import DjangoProductReadRepository
from catalog.infrastructure.django.product_write_repository import DjangoProductWriteRepository


def _product_write_repository():
    return DjangoProductWriteRepository()


def create_product(*, business_id: int, data: dict):
    return CreateProduct(_product_write_repository()).execute(
        business_id=business_id,
        data=data,
    )


def update_product(*, business_id: int, product_id: int, data: dict):
    return UpdateProduct(_product_write_repository()).execute(
        business_id=business_id,
        product_id=product_id,
        data=data,
    )


def get_product_read_model(*, business_id: int, product_id: int) -> dict:
    """Composition entry point for the Catalog product read use case."""
    return GetProductReadModel(DjangoProductReadRepository()).execute(
        business_id=business_id,
        product_id=product_id,
    )
