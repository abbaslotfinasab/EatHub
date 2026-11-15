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


    def test_multiline_reservations_with_reversed_input_order_use_stable_stock_lock_order(self):
        from threading import Event, local
        from time import monotonic

        from django.db.models import Sum

        second_ingredient = Ingredient.objects.create(
            business=self.business, name="Sugar", unit="kg"
        )
        second_stock = InventoryV1Stock.objects.create(
            business=self.business,
            warehouse=self.warehouse,
            ingredient=second_ingredient,
            unit="kg",
            quantity="10",
            average_cost="3",
        )

        first_locked = Event()
        release_first = Event()
        worker_state = local()
        delegate = DjangoReservationRepository()

        class HoldingRepository:
            def __getattr__(self, name):
                return getattr(delegate, name)

            def lock_stock_positions(self, *args, **kwargs):
                result = delegate.lock_stock_positions(*args, **kwargs)
                if worker_state.role == "first":
                    first_locked.set()
                    if not release_first.wait(15):
                        raise TimeoutError("test coordinator did not release first reservation")
                return result

        manager = ManageReservations(HoldingRepository(), DjangoInventoryUnitOfWork())
        prefix = f"reservation_lock_order_{uuid4().hex[:8]}"

        def reserve(role, label, lines):
            close_old_connections()
            worker_state.role = role
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute("SET application_name = %s", [label])
                return manager.create(
                    InventoryExecutionContext(self.business.pk, actor_id=71),
                    warehouse_id=self.warehouse.pk,
                    source_type="manual",
                    source_id=None,
                    reason=f"Multi-line reservation {role}",
                    idempotency_key=uuid4(),
                    lines=lines,
                ), None
            except Exception as error:
                return None, error
            finally:
                connections.close_all()

        def wait_until_blocked(label):
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

        first_lines = [
            {"ingredient_id": self.ingredient.pk, "quantity": "1", "unit": "kg"},
            {"ingredient_id": second_ingredient.pk, "quantity": "1", "unit": "kg"},
        ]
        reversed_lines = list(reversed(first_lines))

        with ThreadPoolExecutor(max_workers=2) as pool:
            first_future = pool.submit(
                reserve, "first", f"{prefix}_first", first_lines
            )
            try:
                self.assertTrue(
                    first_locked.wait(10),
                    "first reservation did not acquire its stock projection locks",
                )
                second_future = pool.submit(
                    reserve, "second", f"{prefix}_second", reversed_lines
                )
                wait_until_blocked(f"{prefix}_second")
            finally:
                release_first.set()
            first_result = first_future.result(timeout=20)
            second_result = second_future.result(timeout=20)

        self.assertIsNone(first_result[1], repr(first_result[1]))
        self.assertIsNone(second_result[1], repr(second_result[1]))
        self.assertEqual(len(first_result[0].lines), 2)
        self.assertEqual(len(second_result[0].lines), 2)
        self.assertEqual(
            InventoryReservation.objects.filter(
                business=self.business, status="active"
            ).count(),
            2,
        )

        totals = {
            row["ingredient_id"]: row["total"]
            for row in InventoryReservationLine.objects.filter(
                reservation__business=self.business,
                reservation__warehouse=self.warehouse,
                reservation__status="active",
            ).values("ingredient_id").annotate(total=Sum("quantity"))
        }
        self.assertEqual(totals, {
            self.ingredient.pk: 2,
            second_ingredient.pk: 2,
        })
        self.stock.refresh_from_db()
        second_stock.refresh_from_db()
        self.assertEqual(str(self.stock.quantity), "10.000000000000")
        self.assertEqual(str(second_stock.quantity), "10.000000000000")

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
