from concurrent.futures import ThreadPoolExecutor
from threading import Event
from time import monotonic
from unittest.mock import patch
from uuid import uuid4

from django.db import close_old_connections, connection, connections
from django.db.models import Sum
from django.test import TransactionTestCase

from accounts.models import Business
from inventory.application.context import InventoryExecutionContext
from inventory.application.exceptions import OperationConflict
from inventory.application.use_cases.manage_reservations import ManageReservations
from inventory.domain.entities.reservation import MANUAL_RESERVATION_SOURCE
from inventory.infrastructure.django.models import (
    InventoryOperation,
    InventoryOperationLine,
    InventoryReservation,
    InventoryReservationLine,
    InventoryV1Stock,
    InventoryV1StockMovement,
)
from inventory.infrastructure.django.operations_service import dispatch_transfer, post_issue
from inventory.infrastructure.django.reservation_repository import DjangoReservationRepository
from inventory.infrastructure.django.repositories import DjangoStockRepository
from inventory.infrastructure.django.unit_of_work import DjangoInventoryUnitOfWork
from inventory.models import Ingredient, Warehouse


class _HoldingReservationRepository:
    """Pause a reservation after it owns the stock-row lock."""

    def __init__(self, delegate, acquired, release):
        self._delegate = delegate
        self._acquired = acquired
        self._release = release

    def __getattr__(self, name):
        return getattr(self._delegate, name)

    def lock_stock_positions(self, *args, **kwargs):
        result = self._delegate.lock_stock_positions(*args, **kwargs)
        self._acquired.set()
        if not self._release.wait(15):
            raise TimeoutError("test coordinator did not release reservation transaction")
        return result


class ReservationVersusIssuePostgreSQLTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        if connection.vendor != "postgresql":
            self.skipTest("Reservation/issue lock race requires PostgreSQL.")
        self.business = Business.objects.create(name="Reservation issue concurrency")
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
        self.destination = Warehouse.objects.create(
            business=self.business, name="Destination"
        )
        self.issue = InventoryOperation.objects.create(
            business=self.business,
            operation_type=InventoryOperation.Type.ISSUE,
            status=InventoryOperation.Status.DRAFT,
            warehouse=self.warehouse,
            reason="Kitchen use",
            created_by_id=1,
        )
        InventoryOperationLine.objects.create(
            operation=self.issue,
            ingredient=self.ingredient,
            quantity="7",
            unit="kg",
        )

    @staticmethod
    def _worker(label, operation):
        close_old_connections()
        db = connections["default"]
        db.ensure_connection()
        with db.cursor() as cursor:
            cursor.execute("SET application_name = %s", [label])
            cursor.execute("SELECT pg_backend_pid()")
            pid = cursor.fetchone()[0]
        try:
            return operation(), pid, None
        except Exception as error:
            return None, pid, error
        finally:
            db.close()

    def _wait_until_blocked(self, label):
        deadline = monotonic() + 15
        while monotonic() < deadline:
            with connections["default"].cursor() as cursor:
                cursor.execute(
                    """SELECT wait_event_type, cardinality(pg_blocking_pids(pid))
                       FROM pg_stat_activity WHERE application_name = %s""",
                    [label],
                )
                row = cursor.fetchone()
            if row and row[0] == "Lock" and row[1] > 0:
                return
        self.fail(f"PostgreSQL did not report a lock wait for {label}.")

    def test_issue_waiting_for_reservation_cannot_consume_reserved_stock(self):
        reservation_locked = Event()
        release_reservation = Event()
        issue_attempting = Event()
        repository = _HoldingReservationRepository(
            DjangoReservationRepository(), reservation_locked, release_reservation
        )
        manager = ManageReservations(repository, DjangoInventoryUnitOfWork())
        context = InventoryExecutionContext(self.business.pk, actor_id=1)
        reservation_key = uuid4()
        prefix = f"res_issue_{uuid4().hex[:8]}"
        reservation_operation = lambda: manager.create(
            context,
            warehouse_id=self.warehouse.pk,
            source_type=MANUAL_RESERVATION_SOURCE,
            source_id=None,
            reason="Reserved for production",
            idempotency_key=reservation_key,
            lines=[{
                "ingredient_id": self.ingredient.pk,
                "quantity": "7",
                "unit": "kg",
            }],
        )

        def issue_operation():
            issue_attempting.set()
            return post_issue(
                business_id=self.business.pk,
                actor_id=1,
                operation_id=self.issue.pk,
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            reservation_future = pool.submit(
                self._worker, f"{prefix}_reservation", reservation_operation
            )
            if not reservation_locked.wait(10):
                release_reservation.set()
                self.fail("reservation did not acquire the stock-row lock")

            issue_future = pool.submit(
                self._worker, f"{prefix}_issue", issue_operation
            )
            try:
                if not issue_attempting.wait(10):
                    self.fail("issue worker did not start")
                self._wait_until_blocked(f"{prefix}_issue")
            finally:
                release_reservation.set()

            reservation_result = reservation_future.result(timeout=20)
            issue_result = issue_future.result(timeout=20)

        self.assertNotEqual(reservation_result[1], issue_result[1])
        self.assertIsNone(reservation_result[2], reservation_result[2])
        self.assertIsNotNone(reservation_result[0])
        self.assertIsInstance(issue_result[2], OperationConflict)

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, 10)
        self.assertEqual(
            InventoryReservation.objects.filter(
                business=self.business,
                status=InventoryReservation.Status.ACTIVE,
            ).count(),
            1,
        )
        reserved = InventoryReservationLine.objects.filter(
            reservation__business=self.business,
            reservation__warehouse=self.warehouse,
            reservation__status=InventoryReservation.Status.ACTIVE,
            ingredient=self.ingredient,
        ).aggregate(total=Sum("quantity"))["total"]
        self.assertEqual(reserved, 7)
        self.assertEqual(
            InventoryV1StockMovement.objects.filter(
                stock=self.stock, movement_type="issue"
            ).count(),
            0,
        )

    def test_transfer_waiting_for_reservation_cannot_dispatch_reserved_stock(self):
        transfer = InventoryOperation.objects.create(
            business=self.business,
            operation_type=InventoryOperation.Type.TRANSFER,
            status=InventoryOperation.Status.DRAFT,
            warehouse=self.warehouse,
            destination_warehouse=self.destination,
            reference="TRANSFER-RESERVATION-RACE",
            created_by_id=1,
        )
        InventoryOperationLine.objects.create(
            operation=transfer,
            ingredient=self.ingredient,
            quantity="7",
            unit="kg",
        )
        reservation_locked = Event()
        release_reservation = Event()
        transfer_attempting = Event()
        repository = _HoldingReservationRepository(
            DjangoReservationRepository(), reservation_locked, release_reservation
        )
        manager = ManageReservations(repository, DjangoInventoryUnitOfWork())
        context = InventoryExecutionContext(self.business.pk, actor_id=1)
        reservation_operation = lambda: manager.create(
            context,
            warehouse_id=self.warehouse.pk,
            source_type=MANUAL_RESERVATION_SOURCE,
            source_id=None,
            reason="Reserved before transfer dispatch",
            idempotency_key=uuid4(),
            lines=[{
                "ingredient_id": self.ingredient.pk,
                "quantity": "7",
                "unit": "kg",
            }],
        )

        def transfer_operation():
            transfer_attempting.set()
            return dispatch_transfer(
                business_id=self.business.pk,
                actor_id=1,
                operation_id=transfer.pk,
            )

        prefix = f"res_transfer_{uuid4().hex[:8]}"
        with ThreadPoolExecutor(max_workers=2) as pool:
            reservation_future = pool.submit(
                self._worker, f"{prefix}_reservation", reservation_operation
            )
            if not reservation_locked.wait(10):
                release_reservation.set()
                self.fail("reservation did not acquire the stock-row lock")

            transfer_future = pool.submit(
                self._worker, f"{prefix}_transfer", transfer_operation
            )
            try:
                if not transfer_attempting.wait(10):
                    self.fail("transfer worker did not start")
                self._wait_until_blocked(f"{prefix}_transfer")
            finally:
                release_reservation.set()

            reservation_result = reservation_future.result(timeout=20)
            transfer_result = transfer_future.result(timeout=20)

        self.assertNotEqual(reservation_result[1], transfer_result[1])
        self.assertIsNone(reservation_result[2], reservation_result[2])
        self.assertIsNotNone(reservation_result[0])
        self.assertIsInstance(transfer_result[2], OperationConflict)

        self.stock.refresh_from_db()
        transfer.refresh_from_db()
        self.assertEqual(self.stock.quantity, 10)
        self.assertEqual(transfer.status, InventoryOperation.Status.DRAFT)
        self.assertEqual(
            InventoryReservation.objects.filter(
                business=self.business,
                status=InventoryReservation.Status.ACTIVE,
            ).count(),
            1,
        )
        reserved = InventoryReservationLine.objects.filter(
            reservation__business=self.business,
            reservation__warehouse=self.warehouse,
            reservation__status=InventoryReservation.Status.ACTIVE,
            ingredient=self.ingredient,
        ).aggregate(total=Sum("quantity"))["total"]
        self.assertEqual(reserved, 7)
        self.assertEqual(
            InventoryV1StockMovement.objects.filter(
                stock=self.stock, movement_type="transfer_dispatch"
            ).count(),
            0,
        )


    def test_issue_first_then_reservation_does_not_deadlock_on_parent_and_stock_locks(self):
        issue_stock_locked = Event()
        release_issue = Event()
        reservation_waiting_for_stock = Event()
        original_save = DjangoStockRepository.save

        def hold_issue_after_stock_lock(repository, stock):
            issue_stock_locked.set()
            if not release_issue.wait(15):
                raise TimeoutError("test coordinator did not release issue transaction")
            return original_save(repository, stock)

        class NotifyingReservationRepository:
            def __init__(self, delegate):
                self.delegate = delegate

            def __getattr__(self, name):
                return getattr(self.delegate, name)

            def lock_stock_positions(self, *args, **kwargs):
                reservation_waiting_for_stock.set()
                return self.delegate.lock_stock_positions(*args, **kwargs)

        manager = ManageReservations(
            NotifyingReservationRepository(DjangoReservationRepository()),
            DjangoInventoryUnitOfWork(),
        )
        context = InventoryExecutionContext(self.business.pk, actor_id=1)
        prefix = f"issue_first_reservation_{uuid4().hex[:8]}"

        def issue_operation():
            return post_issue(
                business_id=self.business.pk,
                actor_id=1,
                operation_id=self.issue.pk,
            )

        def reservation_operation():
            return manager.create(
                context,
                warehouse_id=self.warehouse.pk,
                source_type=MANUAL_RESERVATION_SOURCE,
                source_id=None,
                reason="Competing reservation",
                idempotency_key=uuid4(),
                lines=[{
                    "ingredient_id": self.ingredient.pk,
                    "quantity": "7",
                    "unit": "kg",
                }],
            )

        with patch.object(DjangoStockRepository, "save", hold_issue_after_stock_lock):
            with ThreadPoolExecutor(max_workers=2) as pool:
                issue_future = pool.submit(
                    self._worker, f"{prefix}_issue", issue_operation
                )
                if not issue_stock_locked.wait(10):
                    release_issue.set()
                    self.fail("issue did not acquire the stock-row lock")

                reservation_future = pool.submit(
                    self._worker, f"{prefix}_reservation", reservation_operation
                )
                try:
                    if not reservation_waiting_for_stock.wait(10):
                        self.fail("reservation did not reach its stock-row lock")
                finally:
                    release_issue.set()

                issue_result = issue_future.result(timeout=20)
                reservation_result = reservation_future.result(timeout=20)

        self.assertNotEqual(issue_result[1], reservation_result[1])
        self.assertIsNone(issue_result[2], issue_result[2])
        self.assertIsNotNone(issue_result[0])
        self.assertIsInstance(reservation_result[2], OperationConflict)

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, 3)
        self.assertEqual(
            InventoryReservation.objects.filter(
                business=self.business,
                status=InventoryReservation.Status.ACTIVE,
            ).count(),
            0,
        )
        self.assertEqual(
            InventoryV1StockMovement.objects.filter(
                stock=self.stock, movement_type="issue"
            ).count(),
            1,
        )
