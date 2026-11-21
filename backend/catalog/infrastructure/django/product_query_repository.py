from django.db.models import Q

from catalog.models import Product


class DjangoProductQueryRepository:
    """Django ORM adapter for Catalog Product list and detail reads."""

    def list_for_business(
        self, *, business_id: int, search: str | None, category: str | None,
        status: str | None, page: int, page_size: int,
    ) -> tuple[int, list[Product]]:
        products = Product.objects.filter(business_id=business_id).prefetch_related(
            "allergen_declarations", "dietary_tags",
        )
        if search:
            term = search.strip()
            products = products.filter(Q(name__icontains=term) | Q(sku__icontains=term))
        if category:
            products = products.filter(category__iexact=category.strip())
        if status:
            products = products.filter(status=status)

        count = products.count()
        start = (page - 1) * page_size
        results = list(products.order_by("name", "id")[start:start + page_size])
        return count, results

    def get_for_business(self, *, business_id: int, product_id: int) -> Product | None:
        return Product.objects.filter(
            business_id=business_id,
            pk=product_id,
        ).prefetch_related("allergen_declarations", "dietary_tags").first()
