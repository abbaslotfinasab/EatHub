"""Real PostgreSQL tests for Inventory mutation and idempotency races.

Each worker owns a Django connection. Tests that need a contested row verify
that PostgreSQL reports an actual lock wait before releasing the first worker.
"""

from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from threading import Barrier, Event
from time import monotonic
from uuid import uuid4

from django.db import connections
from django.test import TransactionTestCase
from concurrent.futures import ThreadPoolExecutor

from accounts.models import Business
from inventory.application.commands import (
    AdjustStockCommand,
    OperationIdentityInput,
    ReceiveStockCommand,
    ReverseStockMovementCommand,
)
from inventory.application.context import InventoryExecutionContext
from inventory.application.exceptions import OperationConflict, ResourceNotFound
from inventory.application.use_cases.adjust_stock import AdjustStockUseCase
from inventory.application.use_cases.receive_stock import ReceiveStockUseCase
from inventory.application.use_cases.reverse_stock_movement import (
    ReverseStockMovementUseCase,
)
from inventory.domain.enums.movement import MovementDirection
from inventory.domain.exceptions import (
    MovementAlreadyReversed,
    MovementNotReversible,
    NegativeStock,
    TenantMismatch,
)
from inventory.domain.value_objects.quantity import Quantity
from inventory.domain.value_objects.unit import Unit
from inventory.domain.value_objects.unit_cost import UnitCost
from inventory.infrastructure.django.models import (
    InventoryV1Stock,
    InventoryV1StockMovement,
)
from inventory.infrastructure.django.repositories import (
    DjangoIngredientRepository,
    DjangoStockMovementRepository,
    DjangoStockRepository,
    DjangoWarehouseRepository,
)
from inventory.infrastructure.django.unit_of_work import DjangoInventoryUnitOfWork
from inventory.models import Ingredient as LegacyIngredient
from inventory.models import Warehouse as LegacyWarehouse


class _StockHooks:
    """Test-only hooks around Infrastructure stock access, never App ports."""

    def __init__(self, delegate, *, before=None, after=None):
        self.delegate = delegate
        self.before = before
        self.after = after

    def __getattr__(self, name):
        return getattr(self.delegate, name)

    def _call(self, method, *args):
        if self.before:
            self.before()
        result = method(*args)
        if self.after:
            self.after()
        return result

    def get_for_business(self, *args):
        return self._call(self.delegate.get_for_business, *args)

    def get_or_create_for_business(self, *args):
        return self._call(self.delegate.get_or_create_for_business, *args)


class _MovementHooks:
    def __init__(self, delegate, *, before_save=None, after_save=None):
        self.delegate = delegate
        self.before_save = before_save
        self.after_save = after_save

    def __getattr__(self, name):
        return getattr(self.delegate, name)

    def save(self, movement):
        if self.before_save:
            self.before_save()
        result = self.delegate.save(movement)
        if self.after_save:
            self.after_save()
        return result


class InventoryPostgreSQLConcurrencyTests(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        if connections["default"].vendor != "postgresql":
            raise RuntimeError(
                "Inventory concurrency tests require PostgreSQL; SQLite is not a fallback."
            )
        super().setUpClass()

    def setUp(self):
        self._business_ids = []
        self.business = self._create_business("Concurrency", "inv-concurrency")
        self.warehouse = LegacyWarehouse.objects.create(
            business=self.business, name="Main", code="MAIN", is_default=True
        )
        self.ingredient = LegacyIngredient.objects.create(
            business=self.business,
            name="Flour",
            unit=Unit.KG.value,
            preparation_level="raw",
        )

    def _create_business(self, name, slug):
        business = Business.objects.create(name=name, slug=slug)
        self._business_ids.append(business.pk)
        return business

    def _fixture_teardown(self):
        # The legacy Inventory migration graph leaves a PurchaseOrder table
        # absent from the current model registry. PostgreSQL TRUNCATE flush
        # fails on that table's FK to Business, so remove only this test's rows
        # in dependency order instead of flushing unrelated database tables.
        business_ids = list(self._business_ids)
        if business_ids:
            InventoryV1StockMovement.objects.filter(
                business_id__in=business_ids
            ).delete()
            InventoryV1Stock.objects.filter(business_id__in=business_ids).delete()
            LegacyIngredient.objects.filter(business_id__in=business_ids).delete()
            LegacyWarehouse.objects.filter(business_id__in=business_ids).delete()
            Business.objects.filter(pk__in=business_ids).delete()

    def _identity(self, line, *, kind="receive_stock", source_type="purchase_goods_receipt"):
        return OperationIdentityInput(source_type, 700, line, kind)

    def _context(self, business_id=None):
        return InventoryExecutionContext(business_id or self.business.pk, actor_id=88)

    def _use_case(self, case, stocks=None, movements=None):
        args = (
            DjangoWarehouseRepository(),
            DjangoIngredientRepository(),
            stocks or DjangoStockRepository(),
            movements or DjangoStockMovementRepository(),
            DjangoInventoryUnitOfWork(),
        )
        if case == "receive":
            return ReceiveStockUseCase(*args)
        if case == "adjust":
            return AdjustStockUseCase(*args)
        if case == "reverse":
            return ReverseStockMovementUseCase(*args)
        raise AssertionError(case)

    def _receive(
        self,
        line,
        quantity,
        cost,
        *,
        business_id=None,
        warehouse_id=None,
        ingredient_id=None,
        stocks=None,
        movements=None,
    ):
        command = ReceiveStockCommand(
            warehouse_id=warehouse_id or self.warehouse.pk,
            ingredient_id=ingredient_id or self.ingredient.pk,
            quantity_amount=Decimal(quantity),
            quantity_unit=Unit.KG.value,
            unit_cost_amount=Decimal(cost),
            unit_cost_unit=Unit.KG.value,
            source=self._identity(line),
        )
        return self._use_case("receive", stocks, movements).execute(
            command, self._context(business_id)
        )

    def _adjust(self, line, quantity, direction, *, stocks=None, movements=None):
        command = AdjustStockCommand(
            self.warehouse.pk,
            self.ingredient.pk,
            Quantity(Decimal(quantity), Unit.KG),
            direction,
            "Concurrent physical count",
            self._identity(line, kind="adjust_stock", source_type="inventory_adjustment"),
        )
        return self._use_case("adjust", stocks, movements).execute(command, self._context())

    def _reverse(self, original, line, *, stocks=None, movements=None):
        target = OperationIdentityInput(
            original.source_identity.source_type,
            original.source_identity.source_document_id,
            original.source_identity.source_line_id,
            original.source_identity.operation_kind,
        )
        command = ReverseStockMovementCommand(
            target,
            self._identity(line, kind="reverse_movement", source_type="inventory_reversal"),
            "Concurrent reversal",
        )
        return self._use_case("reverse", stocks, movements).execute(
            command, self._context()
        )

    def _thread(self, label, operation, *, barrier=None):
        from django.db import close_old_connections

        close_old_connections()
        connection = connections["default"]
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SET application_name = %s", [label])
            cursor.execute("SELECT pg_backend_pid()")
            pid = cursor.fetchone()[0]
        try:
            if barrier is not None:
                barrier.wait(timeout=10)
            return operation(), pid, None
        except Exception as error:  # return worker failures for deterministic assertions
            return None, pid, error
        finally:
            connection.close()

    def _wait_until_postgres_blocks(self, label):
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
            Event().wait(0.01)
        self.fail(f"PostgreSQL did not report a lock wait for worker {label}.")

    def _run_contended_stock_operations(self, first, second):
        acquired = Event()
        release_first = Event()
        second_attempting = Event()

        def hold_first():
            acquired.set()
            if not release_first.wait(15):
                raise TimeoutError("test coordinator did not release the first transaction")

        first_stocks = _StockHooks(DjangoStockRepository(), after=hold_first)
        second_stocks = _StockHooks(
            DjangoStockRepository(), before=second_attempting.set
        )
        prefix = f"inv_{uuid4().hex[:8]}"
        with ThreadPoolExecutor(max_workers=2) as pool:
            future_a = pool.submit(self._thread, f"{prefix}_a", first(first_stocks))
            if not acquired.wait(10):
                release_first.set()
                self.fail("first operation did not acquire its Stock projection")
            future_b = pool.submit(self._thread, f"{prefix}_b", second(second_stocks))
            try:
                if not second_attempting.wait(10):
                    self.fail("second operation did not reach its Stock repository")
                self._wait_until_postgres_blocks(f"{prefix}_b")
            finally:
                release_first.set()
            return future_a.result(timeout=20), future_b.result(timeout=20)

    def _stock_row(self, business=None, warehouse=None, ingredient=None):
        return InventoryV1Stock.objects.get(
            business_id=business or self.business.pk,
            warehouse_id=warehouse or self.warehouse.pk,
            ingredient_id=ingredient or self.ingredient.pk,
        )

    def _assert_workers_are_independent(self, *results):
        self.assertEqual(len({result[1] for result in results}), len(results))

    def test_concurrent_first_stock_creation_converges_on_unique_row(self):
        first, second = self._run_contended_stock_operations(
            lambda repo: lambda: self._receive(1, "5", "100", stocks=repo),
            lambda repo: lambda: self._receive(2, "7", "200", stocks=repo),
        )
        self._assert_workers_are_independent(first, second)
        self.assertIsNone(first[2])
        self.assertIsNone(second[2])
        self.assertEqual(first[0].stock_key, second[0].stock_key)
        row = self._stock_row()
        self.assertEqual(InventoryV1Stock.objects.filter(
            business=self.business, warehouse=self.warehouse, ingredient=self.ingredient
        ).count(), 1)
        self.assertEqual(row.quantity, Decimal("12.000000000000"))
        with localcontext() as context:
            context.prec = 100
            expected = (Decimal("5") * 100 + Decimal("7") * 200) / 12
            expected = expected.quantize(Decimal("1e-48"), rounding=ROUND_HALF_EVEN)
        self.assertEqual(row.average_cost, expected)
        self.assertEqual(InventoryV1StockMovement.objects.filter(stock=row).count(), 2)

    def test_concurrent_receipts_preserve_avco_and_movement_order(self):
        self._receive(10, "10", "100")
        first, second = self._run_contended_stock_operations(
            lambda repo: lambda: self._receive(11, "5", "120", stocks=repo),
            lambda repo: lambda: self._receive(12, "7", "200", stocks=repo),
        )
        self._assert_workers_are_independent(first, second)
        self.assertIsNone(first[2])
        self.assertIsNone(second[2])
        row = self._stock_row()
        self.assertEqual(row.quantity, Decimal("22.000000000000"))
        with localcontext() as context:
            context.prec = 100
            first_average = (
                (Decimal("10") * Decimal("100") + Decimal("5") * Decimal("120"))
                / Decimal("15")
            ).quantize(Decimal("1e-48"), rounding=ROUND_HALF_EVEN)
            expected = (
                (Decimal("15") * first_average + Decimal("7") * Decimal("200"))
                / Decimal("22")
            ).quantize(Decimal("1e-48"), rounding=ROUND_HALF_EVEN)
        self.assertEqual(row.average_cost, expected)
        self.assertEqual(InventoryV1StockMovement.objects.filter(stock=row).count(), 3)
        latest = DjangoStockMovementRepository().get_latest_effective_for_stock(
            self.business.pk,
            self._use_case("receive")._stocks.get_for_business(
                self.business.pk, self.warehouse.pk, self.ingredient.pk
            ).key,
        )
        self.assertEqual(latest.source_identity.source_line_id, 12)

    def test_concurrent_adjustments_serialize_and_preserve_average_cost(self):
        self._receive(20, "100", "50")
        first, second = self._run_contended_stock_operations(
            lambda repo: lambda: self._adjust(21, "10", MovementDirection.OUT, stocks=repo),
            lambda repo: lambda: self._adjust(22, "20", MovementDirection.OUT, stocks=repo),
        )
        self._assert_workers_are_independent(first, second)
        self.assertIsNone(first[2])
        self.assertIsNone(second[2])
        row = self._stock_row()
        self.assertEqual(row.quantity, Decimal("70.000000000000"))
        self.assertEqual(row.average_cost, Decimal("50"))
        movements = list(
            InventoryV1StockMovement.objects.filter(stock=row)
            .order_by("id")
            .values_list("direction", "quantity")
        )
        self.assertEqual(
            movements,
            [
                ("in", Decimal("100.000000000000")),
                ("out", Decimal("10.000000000000")),
                ("out", Decimal("20.000000000000")),
            ],
        )

    def test_concurrent_adjustment_in_and_out_both_apply_once(self):
        self._receive(30, "100", "50")
        first, second = self._run_contended_stock_operations(
            lambda repo: lambda: self._adjust(31, "10", MovementDirection.IN, stocks=repo),
            lambda repo: lambda: self._adjust(32, "20", MovementDirection.OUT, stocks=repo),
        )
        self._assert_workers_are_independent(first, second)
        self.assertIsNone(first[2])
        self.assertIsNone(second[2])
        row = self._stock_row()
        self.assertEqual(row.quantity, Decimal("90.000000000000"))
        self.assertEqual(row.average_cost, Decimal("50"))
        movements = list(
            InventoryV1StockMovement.objects.filter(stock=row)
            .order_by("id")
            .values_list("direction", "quantity")
        )
        self.assertEqual(
            movements,
            [
                ("in", Decimal("100.000000000000")),
                ("in", Decimal("10.000000000000")),
                ("out", Decimal("20.000000000000")),
            ],
        )

    def test_negative_stock_race_allows_only_one_outbound(self):
        self._receive(40, "10", "8")
        first, second = self._run_contended_stock_operations(
            lambda repo: lambda: self._adjust(41, "7", MovementDirection.OUT, stocks=repo),
            lambda repo: lambda: self._adjust(42, "7", MovementDirection.OUT, stocks=repo),
        )
        self._assert_workers_are_independent(first, second)
        errors = [result[2] for result in (first, second)]
        self.assertEqual(sum(error is None for error in errors), 1)
        self.assertEqual(sum(isinstance(error, NegativeStock) for error in errors), 1)
        row = self._stock_row()
        self.assertEqual(row.quantity, Decimal("3.000000000000"))
        self.assertGreaterEqual(row.quantity, 0)
        self.assertEqual(InventoryV1StockMovement.objects.filter(stock=row).count(), 2)
        failed_line = 41 if isinstance(errors[0], NegativeStock) else 42
        self.assertFalse(
            InventoryV1StockMovement.objects.filter(
                source_line_id=failed_line,
                source_type="inventory_adjustment",
            ).exists()
        )

    def test_duplicate_source_identity_race_returns_idempotent_result(self):
        first, second = self._run_contended_stock_operations(
            lambda repo: lambda: self._receive(50, "9", "13", stocks=repo),
            lambda repo: lambda: self._receive(50, "9", "13", stocks=repo),
        )
        self._assert_workers_are_independent(first, second)
        self.assertIsNone(first[2])
        self.assertIsNone(second[2])
        self.assertEqual(first[0].stock_key, second[0].stock_key)
        self.assertEqual(sum(bool(result[0].idempotent) for result in (first, second)), 1)
        row = self._stock_row()
        self.assertEqual(row.quantity, Decimal("9.000000000000"))
        self.assertEqual(InventoryV1StockMovement.objects.filter(stock=row).count(), 1)

    def test_conflicting_source_identity_race_is_rejected_after_stock_lock(self):
        first, second = self._run_contended_stock_operations(
            lambda repo: lambda: self._receive(60, "5", "13", stocks=repo),
            lambda repo: lambda: self._receive(60, "6", "13", stocks=repo),
        )
        self._assert_workers_are_independent(first, second)
        errors = [result[2] for result in (first, second)]
        self.assertEqual(sum(error is None for error in errors), 1)
        self.assertEqual(sum(isinstance(error, OperationConflict) for error in errors), 1)
        row = self._stock_row()
        accepted = first[0] if first[2] is None else second[0]
        self.assertEqual(row.quantity, accepted.current_quantity.amount)
        self.assertEqual(InventoryV1StockMovement.objects.filter(stock=row).count(), 1)

    def test_same_source_identity_on_different_stock_keys_uses_unique_constraint(self):
        other_warehouse = LegacyWarehouse.objects.create(
            business=self.business, name="Secondary", code="SECONDARY"
        )
        inserted = Event()
        release_first = Event()
        second_before_insert = Event()

        def hold_after_insert():
            inserted.set()
            if not release_first.wait(15):
                raise TimeoutError("test coordinator did not release inserted movement")

        identity_a = self._identity(70)
        command_a = ReceiveStockCommand(
            warehouse_id=self.warehouse.pk,
            ingredient_id=self.ingredient.pk,
            quantity_amount=Decimal("4"),
            quantity_unit=Unit.KG.value,
            unit_cost_amount=Decimal("3"),
            unit_cost_unit=Unit.KG.value,
            source=identity_a,
        )
        command_b = ReceiveStockCommand(
            warehouse_id=other_warehouse.pk,
            ingredient_id=self.ingredient.pk,
            quantity_amount=Decimal("4"),
            quantity_unit=Unit.KG.value,
            unit_cost_amount=Decimal("3"),
            unit_cost_unit=Unit.KG.value,
            source=identity_a,
        )
        prefix = f"inv_{uuid4().hex[:8]}"
        use_case_a = self._use_case(
            "receive",
            movements=_MovementHooks(DjangoStockMovementRepository(), after_save=hold_after_insert),
        )
        use_case_b = self._use_case(
            "receive",
            movements=_MovementHooks(
                DjangoStockMovementRepository(), before_save=second_before_insert.set
            ),
        )
        with ThreadPoolExecutor(max_workers=2) as pool:
            future_a = pool.submit(
                self._thread,
                f"{prefix}_a",
                lambda: use_case_a.execute(command_a, self._context()),
            )
            if not inserted.wait(10):
                release_first.set()
                self.fail("first operation did not append its uncommitted movement")
            future_b = pool.submit(
                self._thread,
                f"{prefix}_b",
                lambda: use_case_b.execute(command_b, self._context()),
            )
            try:
                if not second_before_insert.wait(10):
                    self.fail("second operation did not reach movement insertion")
                self._wait_until_postgres_blocks(f"{prefix}_b")
            finally:
                release_first.set()
            first, second = future_a.result(timeout=20), future_b.result(timeout=20)

        self._assert_workers_are_independent(first, second)
        self.assertIsNone(first[2])
        self.assertIsInstance(second[2], OperationConflict)
        self.assertEqual(
            InventoryV1StockMovement.objects.filter(
                business=self.business,
                source_type="purchase_goods_receipt",
                source_document_id=700,
                source_line_id=70,
                operation_kind="receive_stock",
            ).count(),
            1,
        )
        self.assertFalse(
            InventoryV1Stock.objects.filter(
                business=self.business,
                warehouse=other_warehouse,
                ingredient=self.ingredient,
            ).exists()
        )

    def test_concurrent_reversal_creates_exactly_one_reversal(self):
        self._receive(80, "10", "5")
        original = DjangoStockMovementRepository().find_by_source_identity_for_business(
            self.business.pk, self._identity(80).to_domain(self.business.pk)
        )
        first, second = self._run_contended_stock_operations(
            lambda repo: lambda: self._reverse(original, 81, stocks=repo),
            lambda repo: lambda: self._reverse(original, 82, stocks=repo),
        )
        self._assert_workers_are_independent(first, second)
        errors = [result[2] for result in (first, second)]
        self.assertEqual(sum(error is None for error in errors), 1)
        self.assertEqual(sum(isinstance(error, MovementAlreadyReversed) for error in errors), 1)
        row = self._stock_row()
        self.assertEqual(row.quantity, Decimal("0"))
        self.assertEqual(InventoryV1StockMovement.objects.filter(
            stock=row, movement_type="reversal"
        ).count(), 1)
        original_after = DjangoStockMovementRepository().find_by_source_identity_for_business(
            self.business.pk, original.source_identity
        )
        self.assertEqual(original_after, original)

        # A later effective movement also makes an older movement ineligible.
        self._receive(83, "1", "6")
        middle = DjangoStockMovementRepository().find_by_source_identity_for_business(
            self.business.pk, self._identity(83).to_domain(self.business.pk)
        )
        self._receive(85, "1", "7")
        with self.assertRaises(MovementNotReversible):
            self._reverse(middle, 84)

    def test_postgresql_rolls_back_projection_and_movement_after_append_failure(self):
        self._receive(90, "3", "4")
        before = self._stock_row()
        before_state = (before.quantity, before.average_cost)

        class FailAfterAppend:
            def __init__(self):
                self.delegate = DjangoStockMovementRepository()

            def __getattr__(self, name):
                return getattr(self.delegate, name)

            def save(self, movement):
                self.delegate.save(movement)
                raise RuntimeError("forced post-append failure")

        with self.assertRaisesRegex(RuntimeError, "post-append"):
            self._receive(
                91,
                "2",
                "9",
                movements=FailAfterAppend(),
            )
        after = self._stock_row()
        self.assertEqual((after.quantity, after.average_cost), before_state)
        self.assertEqual(InventoryV1StockMovement.objects.filter(stock=after).count(), 1)
        self._receive(92, "1", "8")
        self.assertEqual(self._stock_row().quantity, Decimal("4.000000000000"))

    def test_concurrent_tenants_are_scoped_and_source_identity_is_business_scoped(self):
        other_business = self._create_business(
            "Other concurrency", "inv-concurrency-other"
        )
        other_warehouse = LegacyWarehouse.objects.create(
            business=other_business, name="Main", code="OTHER"
        )
        other_ingredient = LegacyIngredient.objects.create(
            business=other_business,
            name="Rice",
            unit=Unit.KG.value,
            preparation_level="raw",
        )
        barrier = Barrier(2)
        # Both independently start after the barrier and use the same logical
        # source identity under different Business ownership.
        prefix = f"inv_{uuid4().hex[:8]}"
        with ThreadPoolExecutor(max_workers=2) as pool:
            future_a = pool.submit(
                self._thread,
                f"{prefix}_a",
                lambda: self._receive(100, "2", "7"),
                barrier=barrier,
            )
            future_b = pool.submit(
                self._thread,
                f"{prefix}_b",
                lambda: self._receive(
                    100,
                    "2",
                    "7",
                    business_id=other_business.pk,
                    warehouse_id=other_warehouse.pk,
                    ingredient_id=other_ingredient.pk,
                ),
                barrier=barrier,
            )
            first, second = future_a.result(timeout=20), future_b.result(timeout=20)
        self._assert_workers_are_independent(first, second)
        self.assertIsNone(first[2])
        self.assertIsNone(second[2])
        self.assertEqual(InventoryV1Stock.objects.filter(quantity=Decimal("2")).count(), 2)
        self.assertEqual(InventoryV1StockMovement.objects.filter(
            source_document_id=700, source_line_id=100
        ).count(), 2)
        self.assertIsNone(
            DjangoStockRepository().get_for_business(
                self.business.pk, other_warehouse.pk, other_ingredient.pk
            )
        )
        with self.assertRaises(ResourceNotFound):
            self._receive(
                101,
                "1",
                "9",
                warehouse_id=other_warehouse.pk,
                ingredient_id=other_ingredient.pk,
            )
        own_movement = DjangoStockMovementRepository().find_by_source_identity_for_business(
            self.business.pk,
            self._identity(100).to_domain(self.business.pk),
        )
        self.assertEqual(own_movement.stock_key.business_id, self.business.pk)
        with self.assertRaises(TenantMismatch):
            DjangoStockMovementRepository().find_by_source_identity_for_business(
                self.business.pk,
                self._identity(100).to_domain(other_business.pk),
            )
