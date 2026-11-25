from unittest.mock import Mock

from django.test import SimpleTestCase

from accounts.application.business_inventory_settings import (
    BusinessInventoryBusinessNotFoundError,
    UpdateBusinessInventorySettings,
)


class UpdateBusinessInventorySettingsTests(SimpleTestCase):
    def setUp(self):
        self.repository = Mock()
        self.use_case = UpdateBusinessInventorySettings(self.repository)

    def test_enables_inventory_for_the_explicit_business(self):
        self.repository.set_inventory_enabled.return_value = True

        result = self.use_case.execute(business_id=41, inventory_enabled=True)

        self.assertTrue(result)
        self.repository.set_inventory_enabled.assert_called_once_with(
            business_id=41,
            enabled=True,
        )

    def test_disables_inventory_for_the_explicit_business(self):
        self.repository.set_inventory_enabled.return_value = True

        result = self.use_case.execute(business_id=52, inventory_enabled=False)

        self.assertFalse(result)
        self.repository.set_inventory_enabled.assert_called_once_with(
            business_id=52,
            enabled=False,
        )

    def test_missing_business_is_reported(self):
        self.repository.set_inventory_enabled.return_value = False

        with self.assertRaises(BusinessInventoryBusinessNotFoundError):
            self.use_case.execute(business_id=99, inventory_enabled=True)
        self.repository.set_inventory_enabled.assert_called_once_with(
            business_id=99,
            enabled=True,
        )

from rest_framework.test import APIClient
from django.test import TestCase

from accounts.infrastructure.django.business_inventory_settings_repository import (
    DjangoBusinessInventorySettingsRepository,
)
from accounts.models import Business, User
from accounts.services.business_service import BusinessService


class DjangoBusinessInventorySettingsRepositoryTests(TestCase):
    def test_update_is_scoped_to_the_requested_business(self):
        first = Business.objects.create(name="Inventory First")
        second = Business.objects.create(name="Inventory Second")

        repository = DjangoBusinessInventorySettingsRepository()
        self.assertTrue(repository.set_inventory_enabled(business_id=first.pk, enabled=True))

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertTrue(first.inventory_enabled)
        self.assertFalse(second.inventory_enabled)

    def test_update_returns_false_for_a_missing_business(self):
        repository = DjangoBusinessInventorySettingsRepository()

        self.assertFalse(repository.set_inventory_enabled(business_id=999999, enabled=True))


class BusinessInventorySettingsApplicationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email="inventory-application-owner@example.test",
            password="test-password",
            name="Inventory Application Owner",
            number="inventory-application-owner",
        )
        self.first_business = BusinessService.create_business(self.owner, "Application First")
        self.second_business = BusinessService.create_business(self.owner, "Application Second")
        self.client.force_authenticate(user=self.owner)
        self.url = "/api/accounts/business/inventory-settings/"

    def test_patch_updates_only_the_explicitly_selected_business(self):
        self.client.credentials(HTTP_X_BUSINESS_ID=str(self.first_business.pk))
        response = self.client.patch(
            self.url, {"inventory_enabled": True}, format="json"
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data, {"inventory_enabled": True})
        self.first_business.refresh_from_db()
        self.second_business.refresh_from_db()
        self.assertTrue(self.first_business.inventory_enabled)
        self.assertFalse(self.second_business.inventory_enabled)
