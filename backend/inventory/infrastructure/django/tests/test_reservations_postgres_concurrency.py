from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event, local
from time import monotonic
from uuid import uuid4

from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase, skipUnlessDBFeature

from accounts.models import Business
from inventory.application.context import InventoryExecutionContext
from inventory.application.exceptions import OperationConflict
from inventory.application.use_cases.manage_reservations import ManageReservations
from inventory.infrastructure.django.models import InventoryReservation, InventoryReservationLine, InventoryV1Stock
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


    def test_multiline_reservations_with_reversed_input_order_serialize_without_deadlock(self):
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

        # Reservation scope locks the shared Warehouse and Ingredients before
        # locking Stock projections. The first worker pauses after the full
        # scope is locked; the reversed-input worker must wait and then proceed.
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


    def test_order_reservation_replacement_serializes_with_release_without_deadlock(self):
        class OrderSource:
            @staticmethod
            def is_active(business_id, order_id):
                return True

            @staticmethod
            def reservation_matches(business_id, order_id, lines):
                return True

        order_id = 991
        existing = InventoryReservation.objects.create(
            business=self.business,
            warehouse=self.warehouse,
            source_type="order",
            source_id=order_id,
            reason="Original order hold",
            status=InventoryReservation.Status.ACTIVE,
            idempotency_key=uuid4(),
            payload_fingerprint="b" * 64,
            created_by_id=71,
        )
        InventoryReservationLine.objects.create(
            reservation=existing,
            ingredient=self.ingredient,
            quantity="4",
            unit="kg",
        )

        release_header_locked = Event()
        continue_release = Event()
        create_source_lookup = Event()
        create_stock_locked = Event()
        worker_state = local()
        delegate = DjangoReservationRepository()

        class CoordinatedRepository:
            def __getattr__(self, name):
                return getattr(delegate, name)

            def get_for_business(self, *args, **kwargs):
                result = delegate.get_for_business(*args, **kwargs)
                if worker_state.role == "release" and kwargs.get("lock"):
                    release_header_locked.set()
                    if not continue_release.wait(15):
                        raise TimeoutError("test coordinator did not resume release")
                return result

            def get_active_source_reservation(self, *args, **kwargs):
                if worker_state.role == "create":
                    create_source_lookup.set()
                return delegate.get_active_source_reservation(*args, **kwargs)

            def lock_stock_positions(self, *args, **kwargs):
                result = delegate.lock_stock_positions(*args, **kwargs)
                if worker_state.role == "create":
                    create_stock_locked.set()
                return result

        repository = CoordinatedRepository()
        context = InventoryExecutionContext(self.business.pk, actor_id=72)
        manager = ManageReservations(repository, DjangoInventoryUnitOfWork(), OrderSource())
        prefix = f"order_res_replace_{uuid4().hex[:8]}"

        def run(role, label, operation):
            close_old_connections()
            worker_state.role = role
            db = connections["default"]
            try:
                db.ensure_connection()
                with db.cursor() as cursor:
                    cursor.execute("SET application_name = %s", [label])
                return operation(), None
            except Exception as error:
                return None, error
            finally:
                db.close()

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

        with ThreadPoolExecutor(max_workers=2) as pool:
            release_future = pool.submit(
                run,
                "release",
                f"{prefix}_release",
                lambda: manager.release(context, existing.pk, uuid4(), "Replace order hold"),
            )
            self.assertTrue(
                release_header_locked.wait(10),
                "release did not lock the reservation header",
            )
            create_future = pool.submit(
                run,
                "create",
                f"{prefix}_create",
                lambda: manager.create_for_order(
                    context,
                    warehouse_id=self.warehouse.pk,
                    order_id=order_id,
                    reason="Replacement order hold",
                    idempotency_key=uuid4(),
                    lines=[{
                        "ingredient_id": self.ingredient.pk,
                        "quantity": "3",
                        "unit": "kg",
                    }],
                ),
            )
            try:
                self.assertTrue(create_source_lookup.wait(10))
                wait_until_blocked(f"{prefix}_create")
                self.assertFalse(
                    create_stock_locked.is_set(),
                    "order reservation creation acquired Stock before the active header lock",
                )
            finally:
                continue_release.set()
            release_result = release_future.result(timeout=20)
            create_result = create_future.result(timeout=20)

        self.assertIsNone(release_result[1], repr(release_result[1]))
        self.assertIsNone(create_result[1], repr(create_result[1]))
        self.assertEqual(release_result[0].status.value, "released")
        self.assertEqual(create_result[0].status.value, "active")
        active = InventoryReservation.objects.filter(
            business=self.business,
            source_type="order",
            source_id=order_id,
            status=InventoryReservation.Status.ACTIVE,
        )
        self.assertEqual(active.count(), 1)
        self.assertEqual(active.get().pk, create_result[0].id)
        self.stock.refresh_from_db()
        self.assertEqual(str(self.stock.quantity), "10.000000000000")

    def test_concurrent_reservation_releases_preserve_the_winning_audit_identity(self):
        reservation = self.reserve()
        context = InventoryExecutionContext(self.business.pk, actor_id=81)
        keys = (uuid4(), uuid4())
        reasons = ("Release from operator A", "Release from operator B")
        barrier = Barrier(2)

        def release(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                manager = ManageReservations(
                    DjangoReservationRepository(), DjangoInventoryUnitOfWork()
                )
                return manager.release(
                    context, reservation.id, keys[index], reasons[index]
                ), None
            except Exception as error:
                return None, error
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [
                future.result(timeout=20)
                for future in (pool.submit(release, 0), pool.submit(release, 1))
            ]

        successes = [(index, result[0]) for index, result in enumerate(results) if result[0] is not None]
        failures = [result[1] for result in results if result[1] is not None]
        self.assertEqual(len(successes), 1)
        self.assertEqual(len(failures), 1)
        self.assertIsInstance(failures[0], OperationConflict)

        winner_index, released = successes[0]
        self.assertEqual(released.status.value, "released")
        self.assertEqual(released.release_reason, reasons[winner_index])
        self.assertEqual(released.released_by_id, 81)

        # A retry with the winning key is idempotent; the losing key cannot
        # overwrite the audit metadata of the already committed release.
        replay = self.use_case.release(
            context, reservation.id, keys[winner_index], reasons[winner_index]
        )
        self.assertEqual(replay.id, released.id)
        self.assertEqual(replay.release_reason, released.release_reason)
        with self.assertRaises(OperationConflict):
            self.use_case.release(
                context, reservation.id, keys[1 - winner_index], reasons[1 - winner_index]
            )

        persisted = InventoryReservation.objects.get(pk=reservation.id)
        self.assertEqual(persisted.status, InventoryReservation.Status.RELEASED)
        self.assertEqual(persisted.release_idempotency_key, keys[winner_index])
        self.assertEqual(persisted.release_reason, reasons[winner_index])
        self.assertEqual(persisted.released_by_id, 81)
        self.assertEqual(InventoryReservationLine.objects.filter(reservation=reservation).count(), 1)

