from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase, skipUnlessDBFeature

from accounts.models import Business
from inventory.application.context import InventoryExecutionContext
from inventory.application.exceptions import OperationConflict
from inventory.application.use_cases.manage_reservations import ManageReservations
from inventory.infrastructure.django.models import InventoryReservation, InventoryV1Stock
from inventory.infrastructure.django.reservation_repository import DjangoReservationRepository
from inventory.infrastructure.django.unit_of_work import DjangoInventoryUnitOfWork
from inventory.models import Ingredient, Warehouse


@skipUnlessDBFeature("has_select_for_update")
class ReservationPostgreSQLConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        if connection.vendor != "postgresql":
            self.skipTest("Reservation concurrency tests require PostgreSQL row locks.")
        self.business = Business.objects.create(name="Reservation concurrency")
        self.warehouse = Warehouse.objects.create(business=self.business, name="Main")
        self.ingredient = Ingredient.objects.create(business=self.business, name="Flour", unit="kg")
        self.stock = InventoryV1Stock.objects.create(
            business=self.business, warehouse=self.warehouse, ingredient=self.ingredient,
            unit="kg", quantity="10", average_cost="4",
        )
        self.use_case = ManageReservations(DjangoReservationRepository(), DjangoInventoryUnitOfWork())

    def reserve(self):
        return self.use_case.create(
            InventoryExecutionContext(self.business.pk, actor_id=1),
            warehouse_id=self.warehouse.pk,
            source_type="manual",
            source_id=None,
            reason="Confirmed order reservation",
            idempotency_key=uuid4(),
            lines=[{"ingredient_id": self.ingredient.pk, "quantity": "7", "unit": "kg"}],
        )

    def test_concurrent_reservations_cannot_claim_the_same_final_stock(self):
        barrier = Barrier(2)

        def run(_request_id):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    return self.reserve()
                except Exception as error:
                    return error
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [future.result(timeout=20) for future in (pool.submit(run, 100), pool.submit(run, 101))]
        self.assertEqual(sum(not isinstance(result, Exception) for result in results), 1)
        self.assertEqual(sum(isinstance(result, OperationConflict) for result in results), 1)
        self.stock.refresh_from_db()
        self.assertEqual(str(self.stock.quantity), "10.000000000000")
        self.assertEqual(InventoryReservation.objects.filter(status="active").count(), 1)

    def test_missing_stock_row_never_allows_concurrent_positive_reservations(self):
        self.stock.delete()
        barrier = Barrier(2)

        def run(_request_id):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    return self.reserve()
                except Exception as error:
                    return error
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [future.result(timeout=20) for future in (pool.submit(run, 200), pool.submit(run, 201))]
        self.assertTrue(all(isinstance(result, OperationConflict) for result in results))
        self.assertEqual(InventoryReservation.objects.count(), 0)
