from unittest import skipUnless

from django.db import IntegrityError, connection, transaction
from django.test import TestCase

from accounts.models import Business
from inventory.infrastructure.django.models import InventoryOperation, InventoryV1Stock
from inventory.models import Ingredient, Warehouse


@skipUnless(connection.vendor == "postgresql", "Tenant integrity triggers are PostgreSQL-only")
class InventoryV1TenantIntegrityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.business = Business.objects.create(
            name="V1 Tenant A", slug="v1-tenant-a-integrity"
        )
        cls.other_business = Business.objects.create(
            name="V1 Tenant B", slug="v1-tenant-b-integrity"
        )
        cls.warehouse = Warehouse.objects.create(
            business=cls.business, name="V1 A warehouse", is_default=True
        )
        cls.other_warehouse = Warehouse.objects.create(
            business=cls.other_business, name="V1 B warehouse", is_default=True
        )
        cls.ingredient = Ingredient.objects.create(
            business=cls.business, name="V1 A ingredient", unit="kg"
        )

    def test_stock_rejects_foreign_warehouse_or_ingredient(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryV1Stock.objects.create(
                    business=self.business,
                    warehouse=self.other_warehouse,
                    ingredient=self.ingredient,
                    unit="kg",
                )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryV1Stock.objects.create(
                    business=self.business,
                    warehouse=self.warehouse,
                    ingredient=Ingredient.objects.create(
                        business=self.other_business,
                        name="V1 foreign ingredient",
                        unit="kg",
                    ),
                    unit="kg",
                )

    def test_transfer_rejects_foreign_destination_warehouse(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryOperation.objects.create(
                    business=self.business,
                    operation_type=InventoryOperation.Type.TRANSFER,
                    status=InventoryOperation.Status.DRAFT,
                    warehouse=self.warehouse,
                    destination_warehouse=self.other_warehouse,
                    created_by_id=1,
                )
