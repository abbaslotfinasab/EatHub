from decimal import Decimal

from django.db import DatabaseError, connection, transaction
from django.test import TransactionTestCase, skipUnless

from accounts.models import Business
from inventory.infrastructure.django.models import (
    InventoryV1Stock,
    InventoryV1StockMovement,
)
from inventory.models import Ingredient, Warehouse


@skipUnless(connection.vendor == "postgresql", "append-only TRUNCATE guard is PostgreSQL-specific")
class StockMovementTruncateGuardTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.business = Business.objects.create(
            name="Append-only truncate guard",
            slug="append-only-truncate-guard",
        )
        self.warehouse = Warehouse.objects.create(
            business=self.business,
            name="Main",
        )
        self.ingredient = Ingredient.objects.create(
            business=self.business,
            name="Flour",
            unit="kg",
        )
        self.stock = InventoryV1Stock.objects.create(
            business=self.business,
            warehouse=self.warehouse,
            ingredient=self.ingredient,
            unit="kg",
            quantity=Decimal("1"),
            average_cost=Decimal("2"),
        )
        self.movement = InventoryV1StockMovement.objects.create(
            business=self.business,
            stock=self.stock,
            movement_type="receipt",
            direction="in",
            quantity=Decimal("1"),
            unit="kg",
            unit_cost=Decimal("2"),
            balance_after=Decimal("1"),
            average_cost_before=Decimal("0"),
            source_type="test",
            source_document_id=1,
            source_line_id=1,
            operation_kind="append_only_test",
            actor_id=1,
        )

    def test_database_rejects_truncate_of_stock_movement_ledger(self):
        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("TRUNCATE TABLE inventory_v1_stock_movement")

        self.assertTrue(
            InventoryV1StockMovement.objects.filter(pk=self.movement.pk).exists()
        )

    def _fixture_teardown(self):
        # Django's TransactionTestCase flush uses TRUNCATE. Temporarily disable
        # user triggers only while the isolated test database is being flushed.
        with connection.cursor() as cursor:
            cursor.execute(
                "ALTER TABLE inventory_v1_stock_movement DISABLE TRIGGER USER"
            )
        try:
            super()._fixture_teardown()
        finally:
            with connection.cursor() as cursor:
                cursor.execute(
                    "ALTER TABLE inventory_v1_stock_movement ENABLE TRIGGER USER"
                )
