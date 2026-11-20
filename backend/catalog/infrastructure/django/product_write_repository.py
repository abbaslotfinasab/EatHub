from django.db import IntegrityError, transaction

from catalog.application.exceptions import ProductSkuConflict
from catalog.models import Product, ProductAllergen, ProductDietaryTag


class DjangoProductWriteRepository:
    """Django ORM adapter for Catalog product create/update operations."""

    @staticmethod
    def _save_restrictions(*, product, data, replace=False):
        allergens = data.pop("allergens", None)
        dietary_tags = data.pop("dietary_tags", None)

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

    def create(self, *, business_id: int, data: dict):
        values = dict(data)
        try:
            with transaction.atomic():
                product = Product.objects.create(
                    business_id=business_id,
                    **{key: value for key, value in values.items()
                       if key not in ("allergens", "dietary_tags")},
                )
                self._save_restrictions(product=product, data=values, replace=True)
                return product
        except IntegrityError as error:
            raise ProductSkuConflict from error

    def update(self, *, business_id: int, product_id: int, data: dict):
        values = dict(data)
        try:
            with transaction.atomic():
                product = Product.objects.select_for_update().filter(
                    business_id=business_id, pk=product_id,
                ).first()
                if product is None:
                    return None
                self._save_restrictions(product=product, data=values)
                for field, value in values.items():
                    setattr(product, field, value)
                if values:
                    product.save(update_fields=(*values.keys(), "updated_at"))
                return product
        except IntegrityError as error:
            raise ProductSkuConflict from error
