from django.db import transaction

from catalog.application.use_cases.create_product import CreateProduct
from catalog.application.use_cases.get_product import GetProduct
from catalog.application.use_cases.get_product_read_model import GetProductReadModel
from catalog.application.use_cases.list_products import ListProducts
from catalog.application.use_cases.resolve_active_products import ResolveActiveProducts
from catalog.application.use_cases.update_product import UpdateProduct
from catalog.infrastructure.django.product_query_repository import DjangoProductQueryRepository
from catalog.infrastructure.django.product_read_repository import DjangoProductReadRepository
from catalog.infrastructure.django.product_write_repository import DjangoProductWriteRepository


def _product_write_repository():
    return DjangoProductWriteRepository()


def _product_query_repository():
    return DjangoProductQueryRepository()


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


def list_products(*, business_id: int, page: int, page_size: int, search=None, category=None, status=None):
    return ListProducts(_product_query_repository()).execute(
        business_id=business_id,
        page=page,
        page_size=page_size,
        search=search,
        category=category,
        status=status,
    )


def get_product(*, business_id: int, product_id: int):
    return GetProduct(_product_query_repository()).execute(
        business_id=business_id,
        product_id=product_id,
    )


def get_product_read_model(*, business_id: int, product_id: int) -> dict:
    """Composition entry point for the Catalog product read use case."""
    return GetProductReadModel(DjangoProductReadRepository()).execute(
        business_id=business_id,
        product_id=product_id,
    )


@transaction.atomic
def resolve_active_products(*, business_id: int, product_ids: set[int]) -> dict:
    """Resolve and lock active products through the Catalog application boundary."""
    return ResolveActiveProducts(DjangoProductReadRepository()).execute(
        business_id=business_id,
        product_ids=product_ids,
    )
