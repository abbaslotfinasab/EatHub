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
