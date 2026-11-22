"""Django-backed lookup queries used by menu write endpoints.

Write orchestration remains in MenuService; this adapter owns the
tenant-scoped reads and response reloading required by Presentation.
"""

from products.models import Menu, MenuItem


class DjangoMenuWriteRepository:
    """Encapsulate tenant-scoped menu and menu-item lookups."""

    def get_menu_for_business(self, business_id, menu_id):
        return Menu.objects.filter(
            business_id=business_id,
            pk=menu_id,
        ).first()

    def get_menu_item_for_business(self, business_id, item_id):
        return (
            MenuItem.objects.select_related("product")
            .filter(business_id=business_id, pk=item_id)
            .first()
        )

    def get_menu_item_for_menu_business(self, business_id, item_id):
        return MenuItem.objects.filter(
            menu__business_id=business_id,
            pk=item_id,
        ).first()

    def get_menu_with_items_for_business(self, business_id, menu_id):
        return (
            Menu.objects.filter(business_id=business_id, pk=menu_id)
            .prefetch_related("items__product")
            .get()
        )
