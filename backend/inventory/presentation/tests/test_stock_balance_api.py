from decimal import Decimal

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Role, User
from inventory.domain.value_objects.unit import Unit
from inventory.infrastructure.django.models import InventoryV1Stock
from inventory.models import Ingredient, Warehouse


@override_settings(USE_SQLITE=True)
class StockBalanceListAPITests(APITestCase):
    endpoint = "/api/inventory/balances/"

    @classmethod
    def setUpTestData(cls):
        cls.business = Business.objects.create(name="Inventory API Business")
        cls.other_business = Business.objects.create(name="Other Inventory Business")
        cls.role = Role.objects.create(
            business=cls.business,
            name="Owner",
            code="OWNER",
        )
        cls.other_role = Role.objects.create(
            business=cls.other_business,
            name="Owner",
            code="OWNER",
        )
        cls.user = User.objects.create_user(
            email="inventory-api@example.com",
            password="unused-test-password",
            name="Inventory API User",
            number="8801",
        )
        Membership.objects.create(
            user=cls.user,
            business=cls.business,
            role=cls.role,
            is_active=True,
        )
        cls.other_user = User.objects.create_user(
            email="no-business@example.com",
            password="unused-test-password",
            name="No Business User",
            number="8802",
        )
        cls.flour = Ingredient.objects.create(
            business=cls.business,
            name="Flour",
            unit=Unit.KG.value,
        )
        cls.rice = Ingredient.objects.create(
            business=cls.business,
            name="Rice",
            unit=Unit.KG.value,
        )
        cls.foreign_ingredient = Ingredient.objects.create(
            business=cls.other_business,
            name="Foreign Flour",
            unit=Unit.KG.value,
        )
        cls.main = Warehouse.objects.create(
            business=cls.business,
            name="Main",
            is_default=True,
        )
        cls.second = Warehouse.objects.create(
            business=cls.business,
            name="Second",
        )
        cls.foreign_warehouse = Warehouse.objects.create(
            business=cls.other_business,
            name="Foreign Warehouse",
        )

    def setUp(self):
        self.client.force_authenticate(self.user)

    def create_stock(
        self,
        *,
        business=None,
        warehouse=None,
        ingredient=None,
        quantity="0",
        average_cost="0",
    ):
        return InventoryV1Stock.objects.create(
            business=business or self.business,
            warehouse=warehouse or self.main,
            ingredient=ingredient or self.flour,
            unit=Unit.KG.value,
            quantity=Decimal(quantity),
            average_cost=Decimal(average_cost),
        )

    def test_requires_authentication_and_active_business_membership(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(self.other_user)
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_returns_only_active_business_data_and_ignores_client_business_id(self):
        own = self.create_stock(quantity="2.500000000000", average_cost="9.125")
        foreign = self.create_stock(
            business=self.other_business,
            warehouse=self.foreign_warehouse,
            ingredient=self.foreign_ingredient,
            quantity="99",
            average_cost="99",
        )

        response = self.client.get(
            self.endpoint,
            {"business_id": self.other_business.pk},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], own.pk)
        self.assertNotEqual(response.data["results"][0]["id"], foreign.pk)
        self.assertEqual(response.data["results"][0]["quantity"], "2.500000000000")
        self.assertEqual(response.data["results"][0]["unit"], "kg")
        self.assertEqual(
            Decimal(response.data["results"][0]["average_cost"]),
            Decimal("9.125"),
        )
        self.assertEqual(response.data["results"][0]["ingredient_name"], "Flour")
        self.assertEqual(response.data["results"][0]["warehouse_name"], "Main")

    def test_filters_validate_ownership_and_filter_results(self):
        main_flour = self.create_stock()
        second_rice = self.create_stock(
            warehouse=self.second,
            ingredient=self.rice,
            quantity="3",
        )

        response = self.client.get(
            self.endpoint,
            {"ingredient_id": self.rice.pk, "warehouse_id": self.second.pk},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], second_rice.pk)
        self.assertNotEqual(response.data["results"][0]["id"], main_flour.pk)

        for params in (
            {"ingredient_id": self.foreign_ingredient.pk},
            {"warehouse_id": self.foreign_warehouse.pk},
            {"ingredient_id": 999999},
            {"warehouse_id": 999999},
        ):
            with self.subTest(params=params):
                invalid = self.client.get(self.endpoint, params)
                self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pagination_is_bounded_and_ordered_and_empty_pages_are_stable(self):
        stocks = [
            self.create_stock(warehouse=warehouse, quantity=str(index))
            for index, warehouse in enumerate(
                [self.main, self.second], start=1
            )
        ]
        page_one = self.client.get(self.endpoint, {"page": 1, "page_size": 1})
        page_two = self.client.get(self.endpoint, {"page": 2, "page_size": 1})
        self.assertEqual(page_one.data["count"], 2)
        self.assertEqual(page_one.data["page"], 1)
        self.assertEqual(page_one.data["page_size"], 1)
        self.assertEqual(page_one.data["results"][0]["id"], stocks[0].pk)
        self.assertEqual(page_two.data["results"][0]["id"], stocks[1].pk)

        empty_page = self.client.get(self.endpoint, {"page": 3, "page_size": 1})
        self.assertEqual(empty_page.status_code, status.HTTP_200_OK)
        self.assertEqual(empty_page.data["count"], 2)
        self.assertEqual(empty_page.data["results"], [])

        for params in (
            {"page": 0},
            {"page": "invalid"},
            {"page_size": 0},
            {"page_size": 101},
            {"ingredient_id": 0},
        ):
            with self.subTest(params=params):
                invalid = self.client.get(self.endpoint, params)
                self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_business_page_has_predictable_response(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {"count": 0, "page": 1, "page_size": 20, "results": []},
        )
