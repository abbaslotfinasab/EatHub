from django.db import transaction
from rest_framework.exceptions import ValidationError

from catalog.models import Product


class ProductCatalogService:
    @staticmethod
    @transaction.atomic
    def resolve_active_products(*, business, product_ids):
        """Resolve reusable Product Catalog identities inside one business."""
        ids = set(product_ids)
        if not ids:
            return {}

        products = Product.objects.select_for_update().filter(
            business=business,
            status=Product.Status.ACTIVE,
            pk__in=ids,
        )
        resolved = {product.pk: product for product in products}
        if ids != set(resolved):
            raise ValidationError({
                "product_id": "Select an active product belonging to this business."
            })
        return resolved
