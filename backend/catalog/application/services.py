from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from catalog.models import Product


class ProductCatalogService:
    @staticmethod
    def create(*, business, validated_data):
        try:
            with transaction.atomic():
                return Product.objects.create(business=business, **validated_data)
        except IntegrityError as error:
            raise ValidationError({"sku": "This SKU is already used in this business."}) from error

    @staticmethod
    def update(*, product, validated_data):
        try:
            with transaction.atomic():
                for field, value in validated_data.items():
                    setattr(product, field, value)
                product.save(update_fields=(*validated_data.keys(), "updated_at"))
                return product
        except IntegrityError as error:
            raise ValidationError({"sku": "This SKU is already used in this business."}) from error


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
