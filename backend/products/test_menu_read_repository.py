from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Role, User
from products.models import Menu, MenuItem


class MenuReadRepositoryApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="menu-read@example.test",
            password="test-password",
            name="Menu Read User",
            number="97001",
        )
        self.business = Business.objects.create(name="Menu Read Business")
        self.other_business = Business.objects.create(name="Other Menu Business")
        role = Role.objects.create(
            business=self.business,
            name="Owner",
            code="OWNER",
        )
        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=role,
            is_active=True,
        )
        self.first_menu = Menu.objects.create(
            business=self.business,
            name="First Menu",
            category="Food",
            sort_order=1,
        )
        self.second_menu = Menu.objects.create(
            business=self.business,
            name="Second Menu",
            category="Food",
            sort_order=2,
        )
        self.foreign_menu = Menu.objects.create(
            business=self.other_business,
            name="Foreign Menu",
            category="Food",
            sort_order=0,
        )
        MenuItem.objects.create(
            business=self.business,
            menu=self.first_menu,
            name="Burger",
            price=Decimal("12.00"),
        )
        self.client.force_authenticate(self.user)
        self.client.defaults["HTTP_X_BUSINESS_ID"] = str(self.business.id)

    def test_menu_list_is_tenant_scoped_and_ordered(self):
        response = self.client.get("/api/products/menus/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [menu["id"] for menu in response.data],
            [self.first_menu.id, self.second_menu.id],
        )
        self.assertNotIn(
            self.foreign_menu.id,
            [menu["id"] for menu in response.data],
        )

    def test_menu_detail_is_tenant_scoped(self):
        response = self.client.get(
            f"/api/products/menus/{self.foreign_menu.id}/"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_public_menu_keeps_menu_order_and_payload(self):
        response = self.client.get(
            f"/api/products/{self.business.slug}/menu/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["restaurant"]["id"], self.business.id)
        self.assertEqual(
            [menu["id"] for menu in response.data["menus"]],
            [self.first_menu.id, self.second_menu.id],
        )
        self.assertEqual(
            response.data["menus"][0]["items"][0]["name"],
            "Burger",
        )

    def test_public_menu_hides_inactive_business(self):
        self.business.is_active = False
        self.business.save(update_fields=["is_active"])

        response = self.client.get(
            f"/api/products/{self.business.slug}/menu/"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
