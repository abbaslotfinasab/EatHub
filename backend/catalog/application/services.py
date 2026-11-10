from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from catalog.models import Product, ProductAllergen, ProductDietaryTag


class ProductNotFound(Exception):
    """A Product does not exist inside the requested business."""


class ProductCatalogService:
    @staticmethod
    def _save_restrictions(*, product, validated_data, replace=False):
        allergens = validated_data.pop("allergens", None)
        dietary_tags = validated_data.pop("dietary_tags", None)

        if replace or allergens is not None:
            product.allergen_declarations.all().delete()
            ProductAllergen.objects.bulk_create([
                ProductAllergen(product=product, **item) for item in (allergens or [])
            ])

        if replace or dietary_tags is not None:
            product.dietary_tags.all().delete()
            ProductDietaryTag.objects.bulk_create([
                ProductDietaryTag(product=product, code=code) for code in (dietary_tags or [])
            ])

    @staticmethod
    def create(*, business, validated_data):
        data = dict(validated_data)
        try:
            with transaction.atomic():
                product = Product.objects.create(business=business, **{
                    key: value for key, value in data.items()
                    if key not in ("allergens", "dietary_tags")
                })
                ProductCatalogService._save_restrictions(
                    product=product, validated_data=data, replace=True
                )
                return product
        except IntegrityError as error:
            raise ValidationError({"sku": "This SKU is already used in this business."}) from error

    @staticmethod
    def update(*, product, validated_data):
        data = dict(validated_data)
        try:
            with transaction.atomic():
                ProductCatalogService._save_restrictions(
                    product=product, validated_data=data
                )
                for field, value in data.items():
                    setattr(product, field, value)
                if data:
                    product.save(update_fields=(*data.keys(), "updated_at"))
                return product
        except IntegrityError as error:
            raise ValidationError({"sku": "This SKU is already used in this business."}) from error

    @staticmethod
    def get_product_read_model_for_business(*, business_id: int, product_id: int):
        """Return Catalog-owned display and allergen data without exposing ORM objects."""
        product = Product.objects.filter(
            business_id=business_id,
            pk=product_id,
        ).prefetch_related("allergen_declarations").first()
        if product is None:
            raise ProductNotFound("Product does not exist in this business.")
        return {
            "name": product.name,
            "allergens": tuple(
                {"code": item.code, "presence": item.presence}
                for item in product.allergen_declarations.all()
            ),
        }

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
