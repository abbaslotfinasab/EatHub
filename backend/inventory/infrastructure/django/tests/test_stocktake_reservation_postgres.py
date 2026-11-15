from decimal import Decimal
from uuid import uuid4

from django.db import connection
from django.test import TransactionTestCase, skipUnlessDBFeature

from accounts.models import Business
from inventory.application.exceptions import OperationConflict
from inventory.infrastructure.django.models import (
    InventoryOperation,
    InventoryReservation,
    InventoryReservationLine,
    InventoryV1Stock,
    InventoryV1StockMovement,
)
from inventory.infrastructure.django.operations_service import (
    approve_stocktake,
    create_operation,
)
from inventory.models import Ingredient, Warehouse


@skipUnlessDBFeature("has_select_for_update")
class StocktakeReservationPostgreSQLTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        if connection.vendor != "postgresql":
            self.skipTest("Stocktake/reservation consistency requires PostgreSQL.")
        self.business = Business.objects.create(name="Stocktake reservation guard")
        self.warehouse = Warehouse.objects.create(business=self.business, name="Main")
        self.ingredient = Ingredient.objects.create(
            business=self.business, name="Flour", unit="kg"
        )
        self.stock = InventoryV1Stock.objects.create(
            business=self.business,
            warehouse=self.warehouse,
            ingredient=self.ingredient,
            unit="kg",
            quantity="10",
            average_cost="4",
        )

    def _stocktake(self, counted_quantity):
        return create_operation(
            business_id=self.business.pk,
            actor_id=71,
            operation_type=InventoryOperation.Type.STOCKTAKE,
            warehouse_id=self.warehouse.pk,
            lines=[{
                "ingredient_id": self.ingredient.pk,
                "quantity": "0",
                "unit": "kg",
                "counted_quantity": str(counted_quantity),
            }],
        )

    def _reserve(self, quantity):
        reservation = InventoryReservation.objects.create(
            business=self.business,
            warehouse=self.warehouse,
            source_type="manual",
            source_id=None,
            reason="Reserved for production",
            status=InventoryReservation.Status.ACTIVE,
            idempotency_key=uuid4(),
            payload_fingerprint="a" * 64,
            created_by_id=71,
        )
        InventoryReservationLine.objects.create(
            reservation=reservation,
            ingredient=self.ingredient,
            quantity=Decimal(quantity),
            unit="kg",
        )
        return reservation

    def test_approval_rejects_count_below_active_reservations_atomically(self):
        stocktake = self._stocktake("5")
        self._reserve("7")

        with self.assertRaisesRegex(
            OperationConflict, "below active reservations"
        ):
            approve_stocktake(
                business_id=self.business.pk,
                actor_id=72,
                operation_id=stocktake.pk,
            )

        self.stock.refresh_from_db()
        stocktake.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("10"))
        self.assertEqual(stocktake.status, InventoryOperation.Status.DRAFT)
        self.assertEqual(
            InventoryV1StockMovement.objects.filter(
                source_type="inventory_stocktake",
                source_document_id=stocktake.pk,
            ).count(),
            0,
        )

    def test_approval_allows_count_equal_to_active_reservations(self):
        stocktake = self._stocktake("7")
        self._reserve("7")

        approved = approve_stocktake(
            business_id=self.business.pk,
            actor_id=73,
            operation_id=stocktake.pk,
        )

        self.stock.refresh_from_db()
        self.assertEqual(approved.status, InventoryOperation.Status.APPROVED)
        self.assertEqual(self.stock.quantity, Decimal("7"))
        self.assertEqual(
            InventoryV1StockMovement.objects.filter(
                source_type="inventory_stocktake",
                source_document_id=stocktake.pk,
                movement_type="adjustment",
            ).count(),
            1,
        )
