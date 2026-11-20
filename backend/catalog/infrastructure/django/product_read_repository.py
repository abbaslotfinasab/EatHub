from catalog.models import Product


class DjangoProductReadRepository:
    """Django ORM adapter for Catalog product read projections."""

    def get_read_model_for_business(self, *, business_id: int, product_id: int) -> dict | None:
        product = Product.objects.filter(
            business_id=business_id,
            pk=product_id,
        ).prefetch_related("allergen_declarations").first()
        if product is None:
            return None
        return {
            "name": product.name,
            "allergens": tuple(
                {"code": item.code, "presence": item.presence}
                for item in product.allergen_declarations.all()
            ),
        }
