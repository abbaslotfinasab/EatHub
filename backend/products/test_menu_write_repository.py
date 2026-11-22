from decimal import Decimal

from django.test import TestCase

from accounts.models import Business
from products.infrastructure.django.menu_write_repository import (
    DjangoMenuWriteRepository,
)
from products.models import Menu, MenuItem


class DjangoMenuWriteRepositoryTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Menu Write Business")
        self.other_business = Business.objects.create(name="Other Menu Write Business")
        self.menu = Menu.objects.create(
            business=self.business,
            name="Lunch",
            category="Food",
        )
        self.foreign_menu = Menu.objects.create(
            business=self.other_business,
            name="Foreign Lunch",
            category="Food",
        )
        self.item = MenuItem.objects.create(
            business=self.business,
            menu=self.menu,
            name="Burger",
            price=Decimal("12.00"),
        )
        self.foreign_item = MenuItem.objects.create(
            business=self.other_business,
            menu=self.foreign_menu,
            name="Foreign Burger",
            price=Decimal("13.00"),
        )
        self.repository = DjangoMenuWriteRepository()

    def test_menu_lookup_is_tenant_scoped(self):
        self.assertEqual(
            self.repository.get_menu_for_business(self.business.pk, self.menu.pk).pk,
            self.menu.pk,
        )
        self.assertIsNone(
            self.repository.get_menu_for_business(self.business.pk, self.foreign_menu.pk)
        )

    def test_menu_item_lookup_is_tenant_scoped_and_selects_product(self):
        item = self.repository.get_menu_item_for_business(
            self.business.pk, self.item.pk
        )

        self.assertEqual(item.pk, self.item.pk)
        self.assertIn("product", item._state.fields_cache)
        self.assertIsNone(
            self.repository.get_menu_item_for_business(
                self.business.pk, self.foreign_item.pk
            )
        )

    def test_menu_item_lookup_by_menu_business_preserves_scope(self):
        item = self.repository.get_menu_item_for_menu_business(
            self.business.pk, self.item.pk
        )

        self.assertEqual(item.pk, self.item.pk)
        self.assertIsNone(
            self.repository.get_menu_item_for_menu_business(
                self.business.pk, self.foreign_item.pk
            )
        )

    def test_menu_response_reload_prefetches_items_and_products(self):
        menu = self.repository.get_menu_with_items_for_business(
            self.business.pk, self.menu.pk
        )

        self.assertIn("items", menu._prefetched_objects_cache)
        item = menu.items.all()[0]
        self.assertIn("product", item._state.fields_cache)

    def test_response_reload_does_not_cross_business_boundary(self):
        with self.assertRaises(Menu.DoesNotExist):
            self.repository.get_menu_with_items_for_business(
                self.business.pk, self.foreign_menu.pk
            )
