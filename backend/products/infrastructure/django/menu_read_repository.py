"""Django-backed read queries for tenant and public restaurant menus."""

from accounts.models import Business
from products.models import Menu


class DjangoMenuReadRepository:
    """Encapsulate menu read queries and their loading strategy."""

    def list_for_business(self, business_id):
        return (
            Menu.objects.filter(business_id=business_id)
            .prefetch_related("items__product")
            .order_by("sort_order")
        )

    def get_for_business(self, business_id, menu_id):
        return (
            Menu.objects.filter(business_id=business_id)
            .prefetch_related("items__product")
            .filter(pk=menu_id)
            .first()
        )

    def get_active_business_by_slug(self, slug):
        return Business.objects.filter(slug=slug, is_active=True).first()

    def list_public_for_business(self, business_id):
        return (
            Menu.objects.filter(business_id=business_id)
            .prefetch_related("items")
            .order_by("sort_order")
        )
