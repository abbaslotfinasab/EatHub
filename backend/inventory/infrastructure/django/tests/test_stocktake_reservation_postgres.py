from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Event
from time import monotonic
from uuid import uuid4
from unittest.mock import patch

from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase, skipUnlessDBFeature

from accounts.models import Business
from inventory.application.context import InventoryExecutionContext
from inventory.application.exceptions import OperationConflict
from inventory.application.use_cases.manage_reservations import ManageReservations
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
from inventory.infrastructure.django.reservation_repository import DjangoReservationRepository
from inventory.infrastructure.django.repositories import DjangoStockRepository
from inventory.infrastructure.django.unit_of_work import DjangoInventoryUnitOfWork
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

    def test_stocktake_approval_serializes_before_new_reservation_and_revalidates_balance(self):
        stocktake = self._stocktake("8")
        stock_locked = Event()
        release_stocktake = Event()
        reservation_manager = ManageReservations(
            DjangoReservationRepository(), DjangoInventoryUnitOfWork()
        )
        original_save = DjangoStockRepository.save

        def hold_stocktake_save(repository, stock):
            stock_locked.set()
            if not release_stocktake.wait(15):
                raise TimeoutError("test coordinator did not release stocktake approval")
            return original_save(repository, stock)

        def create_reservation():
            close_old_connections()
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute(
                        "SET application_name = %s", ["stocktake-reservation-race"]
                    )
                return reservation_manager.create(
                    InventoryExecutionContext(self.business.pk, actor_id=74),
                    warehouse_id=self.warehouse.pk,
                    source_type="manual",
                    source_id=None,
                    reason="Concurrent stocktake reservation",
                    idempotency_key=uuid4(),
                    lines=[{
                        "ingredient_id": self.ingredient.pk,
                        "quantity": "9",
                        "unit": "kg",
                    }],
                ), None
            except Exception as error:
                return None, error
            finally:
                connections.close_all()

        def wait_until_blocked(application_name):
            deadline = monotonic() + 15
            while monotonic() < deadline:
                with connections["default"].cursor() as cursor:
                    cursor.execute(
                        """SELECT wait_event_type, cardinality(pg_blocking_pids(pid))
                           FROM pg_stat_activity WHERE application_name = %s""",
                        [application_name],
                    )
                    row = cursor.fetchone()
                if row and row[0] == "Lock" and row[1] > 0:
                    return
            self.fail(f"PostgreSQL did not report a lock wait for {application_name}.")

        def approve():
            close_old_connections()
            try:
                return approve_stocktake(
                    business_id=self.business.pk,
                    actor_id=75,
                    operation_id=stocktake.pk,
                ), None
            except Exception as error:
                return None, error
            finally:
                connections.close_all()

        with patch.object(DjangoStockRepository, "save", hold_stocktake_save):
            with ThreadPoolExecutor(max_workers=2) as pool:
                approval_future = pool.submit(approve)
                try:
                    self.assertTrue(
                        stock_locked.wait(10),
                        "stocktake approval did not reach the locked stock position",
                    )
                    reservation_future = pool.submit(create_reservation)
                    wait_until_blocked("stocktake-reservation-race")
                finally:
                    release_stocktake.set()
                approval_result = approval_future.result(timeout=20)
                reservation_result = reservation_future.result(timeout=20)

        self.assertIsNone(approval_result[1], repr(approval_result[1]))
        self.assertEqual(approval_result[0].status, InventoryOperation.Status.APPROVED)
        self.assertIsInstance(reservation_result[1], OperationConflict)
        self.assertIn("Insufficient available stock", str(reservation_result[1]))
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("8"))
        self.assertEqual(
            InventoryReservation.objects.filter(
                business=self.business, status=InventoryReservation.Status.ACTIVE
            ).count(),
            0,
        )


    def test_opening_stock_first_serializes_before_reservation_and_exposes_committed_balance(self):
        from threading import local

        from inventory.infrastructure.django import operations_service

        self.stock.quantity = Decimal("0")
        self.stock.average_cost = Decimal("0")
        self.stock.save(update_fields=("quantity", "average_cost"))

        stock_locked = Event()
        release_opening = Event()
        worker_state = local()
        original_stock = operations_service._stock
        reservation_manager = ManageReservations(
            DjangoReservationRepository(), DjangoInventoryUnitOfWork()
        )

        def hold_opening_after_stock_lock(*args, **kwargs):
            result = original_stock(*args, **kwargs)
            if worker_state.role == "opening":
                stock_locked.set()
                if not release_opening.wait(15):
                    raise TimeoutError("test coordinator did not release opening stock")
            return result

        def open_stock():
            close_old_connections()
            worker_state.role = "opening"
            try:
                return operations_service.create_opening_stock(
                    business_id=self.business.pk,
                    actor_id=76,
                    warehouse_id=self.warehouse.pk,
                    reference="OPEN-BEFORE-RESERVATION",
                    lines=[{
                        "ingredient_id": self.ingredient.pk,
                        "quantity": "10",
                        "unit": "kg",
                        "unit_cost": "4",
                    }],
                ), None
            except Exception as error:
                return None, error
            finally:
                connections.close_all()

        def create_reservation():
            close_old_connections()
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute(
                        "SET application_name = %s",
                        ["opening-reservation-race"],
                    )
                return reservation_manager.create(
                    InventoryExecutionContext(self.business.pk, actor_id=77),
                    warehouse_id=self.warehouse.pk,
                    source_type="manual",
                    source_id=None,
                    reason="Reservation after opening balance",
                    idempotency_key=uuid4(),
                    lines=[{
                        "ingredient_id": self.ingredient.pk,
                        "quantity": "8",
                        "unit": "kg",
                    }],
                ), None
            except Exception as error:
                return None, error
            finally:
                connections.close_all()

        def wait_until_blocked(application_name):
            deadline = monotonic() + 15
            while monotonic() < deadline:
                with connections["default"].cursor() as cursor:
                    cursor.execute(
                        """SELECT wait_event_type, cardinality(pg_blocking_pids(pid))
                           FROM pg_stat_activity WHERE application_name = %s""",
                        [application_name],
                    )
                    row = cursor.fetchone()
                if row and row[0] == "Lock" and row[1] > 0:
                    return
            self.fail(f"PostgreSQL did not report a lock wait for {application_name}.")

        with patch.object(
            operations_service, "_stock", side_effect=hold_opening_after_stock_lock
        ):
            with ThreadPoolExecutor(max_workers=2) as pool:
                opening_future = pool.submit(open_stock)
                try:
                    self.assertTrue(
                        stock_locked.wait(10),
                        "opening stock did not lock its stock position",
                    )
                    reservation_future = pool.submit(create_reservation)
                    wait_until_blocked("opening-reservation-race")
                finally:
                    release_opening.set()
                opening_result = opening_future.result(timeout=20)
                reservation_result = reservation_future.result(timeout=20)

        self.assertIsNone(opening_result[1], repr(opening_result[1]))
        self.assertEqual(opening_result[0].status, InventoryOperation.Status.POSTED)
        self.assertIsNone(reservation_result[1], repr(reservation_result[1]))
        self.assertEqual(reservation_result[0].status, "active")
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("10"))
        self.assertEqual(
            InventoryV1StockMovement.objects.filter(
                stock=self.stock, movement_type="opening_balance"
            ).count(),
            1,
        )
        self.assertEqual(
            InventoryReservationLine.objects.filter(
                reservation_id=reservation_result[0].id,
                ingredient=self.ingredient,
                quantity=Decimal("8"),
            ).count(),
            1,
        )
