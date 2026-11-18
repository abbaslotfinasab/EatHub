from decimal import Decimal
from unittest import skipUnless

from django.db import IntegrityError, connection, transaction
from django.test import TestCase

from accounts.models import Business
from inventory.infrastructure.django.models import (
    InventoryV1Stock,
    InventoryV1StockMovement,
)
from inventory.models import Ingredient, Warehouse


@skipUnless(
    connection.vendor == "postgresql",
    "Reversal reference integrity trigger is PostgreSQL-specific",
)
class StockMovementReversalReferenceIntegrityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.business = Business.objects.create(
            name="Reversal reference integrity",
            slug="reversal-reference-integrity",
        )
        cls.warehouse = Warehouse.objects.create(
            business=cls.business,
            name="Main",
        )
        cls.other_warehouse = Warehouse.objects.create(
            business=cls.business,
            name="Secondary",
        )
        cls.ingredient = Ingredient.objects.create(
            business=cls.business,
            name="Flour",
            unit="kg",
        )
        cls.stock = InventoryV1Stock.objects.create(
            business=cls.business,
            warehouse=cls.warehouse,
            ingredient=cls.ingredient,
            unit="kg",
            quantity=Decimal("1"),
            average_cost=Decimal("2"),
        )
        cls.other_stock = InventoryV1Stock.objects.create(
            business=cls.business,
            warehouse=cls.other_warehouse,
            ingredient=cls.ingredient,
            unit="kg",
            quantity=Decimal("1"),
            average_cost=Decimal("2"),
        )
        cls.original = InventoryV1StockMovement.objects.create(
            business=cls.business,
            stock=cls.stock,
            movement_type="receipt",
            direction="in",
            quantity=Decimal("1"),
            unit="kg",
            unit_cost=Decimal("2"),
            balance_after=Decimal("1"),
            average_cost_before=Decimal("0"),
            source_type="receipt",
            source_document_id=100,
            source_line_id=1,
            operation_kind="receive_stock",
        )

    def create_reversal(self, *, stock, target_document_id):
        return InventoryV1StockMovement.objects.create(
            business=self.business,
            stock=stock,
            movement_type="reversal",
            direction="out",
            quantity=Decimal("1"),
            unit="kg",
            unit_cost=Decimal("2"),
            balance_after=Decimal("0"),
            average_cost_before=Decimal("2"),
            source_type="reversal",
            source_document_id=200,
            source_line_id=1,
            operation_kind="reverse_stock",
            actor_id=1,
            reverses_source_type="receipt",
            reverses_source_document_id=target_document_id,
            reverses_source_line_id=1,
            reverses_operation_kind="receive_stock",
        )

    def test_database_rejects_reversal_of_missing_source_identity(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_reversal(
                    stock=self.stock,
                    target_document_id=999,
                )

        self.assertEqual(InventoryV1StockMovement.objects.count(), 1)

    def test_database_rejects_reversal_source_from_another_stock(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_reversal(
                    stock=self.other_stock,
                    target_document_id=100,
                )

        self.assertEqual(InventoryV1StockMovement.objects.count(), 1)
