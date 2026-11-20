from decimal import Decimal
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event, local
from time import monotonic
from unittest.mock import patch

from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase, skipUnlessDBFeature

from accounts.models import Business
from inventory.infrastructure.django.models import (
    InventoryOperation, InventoryOperationLine, InventoryV1Stock,
    InventoryV1StockMovement,
)
from inventory.application.commands import (
    OperationIdentityInput,
    ReverseStockMovementCommand,
)
from inventory.application.context import InventoryExecutionContext
from inventory.application.use_cases.reverse_stock_movement import ReverseStockMovementUseCase
from inventory.domain.value_objects.stock_key import StockKey
from inventory.infrastructure.django.unit_of_work import DjangoInventoryUnitOfWork
from inventory.infrastructure.django.repositories import (
    DjangoIngredientRepository,
    DjangoStockMovementRepository,
    DjangoStockRepository,
    DjangoWarehouseRepository,
)
from inventory.infrastructure.django.operations_service import (
    approve_stocktake,
    create_opening_stock,
    create_operation,
    cancel_operation,
    dispatch_transfer,
    receive_transfer,
    post_issue,
    update_stocktake_counts,
)
from inventory.application.exceptions import OperationConflict
from inventory.infrastructure.django.master_data_repository import DjangoMasterDataRepository
from inventory.models import Ingredient, Warehouse
from inventory.domain.exceptions import NegativeStock
from inventory.infrastructure.django.operations_service import OperationInputError


@skipUnlessDBFeature("has_select_for_update")
class InventoryOperationPostgreSQLConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        if connection.vendor != "postgresql":
            self.skipTest("Inventory operation row-lock test requires PostgreSQL.")
        self.business = Business.objects.create(name="Operation concurrency")
        self.warehouse = Warehouse.objects.create(business=self.business, name="Main")
        self.ingredient = Ingredient.objects.create(business=self.business, name="Flour", unit="kg")
        self.stock = InventoryV1Stock.objects.create(
            business=self.business, warehouse=self.warehouse, ingredient=self.ingredient,
            unit="kg", quantity="10", average_cost="4",
        )
        self.operation = InventoryOperation.objects.create(
            business=self.business, operation_type=InventoryOperation.Type.ISSUE,
            status=InventoryOperation.Status.DRAFT, warehouse=self.warehouse,
            reason="Kitchen use", created_by_id=1,
        )
        InventoryOperationLine.objects.create(
            operation=self.operation, ingredient=self.ingredient,
            quantity="3", unit="kg",
        )

    def test_latest_effective_movement_skips_reversal_and_reversed_source(self):
        first = InventoryV1StockMovement.objects.create(
            business=self.business, stock=self.stock, movement_type="receipt",
            direction="in", quantity=Decimal("4"), unit="kg", unit_cost=Decimal("3"),
            balance_after=Decimal("4"), average_cost_before=Decimal("0"),
            source_type="test_receipt", source_document_id=101, source_line_id=1,
            operation_kind="receive_stock", actor_id=1,
        )
        second = InventoryV1StockMovement.objects.create(
            business=self.business, stock=self.stock, movement_type="receipt",
            direction="in", quantity=Decimal("1"), unit="kg", unit_cost=Decimal("9"),
            balance_after=Decimal("5"), average_cost_before=Decimal("3"),
            source_type="test_receipt", source_document_id=102, source_line_id=1,
            operation_kind="receive_stock", actor_id=1,
        )
        InventoryV1StockMovement.objects.create(
            business=self.business, stock=self.stock, movement_type="reversal",
            direction="out", quantity=Decimal("1"), unit="kg", unit_cost=Decimal("9"),
            balance_after=Decimal("4"), average_cost_before=Decimal("4"),
            source_type="test_reversal", source_document_id=201, source_line_id=1,
            operation_kind="reverse_movement", reverses_source_type=second.source_type,
            reverses_source_document_id=second.source_document_id,
            reverses_source_line_id=second.source_line_id,
            reverses_operation_kind=second.operation_kind, actor_id=1,
        )

        latest = DjangoStockMovementRepository().get_latest_effective_for_stock(
            self.business.pk,
            StockKey(self.business.pk, self.warehouse.pk, self.ingredient.pk),
        )

        self.assertIsNotNone(latest)
        self.assertEqual(latest.source_identity.source_document_id, first.source_document_id)

    def test_concurrent_reversal_requests_append_only_one_reversal(self):
        self.stock.quantity = Decimal("5")
        self.stock.average_cost = Decimal("4.2")
        self.stock.save(update_fields=("quantity", "average_cost"))
        InventoryV1StockMovement.objects.create(
            business=self.business, stock=self.stock, movement_type="receipt",
            direction="in", quantity=Decimal("4"), unit="kg", unit_cost=Decimal("3"),
            balance_after=Decimal("4"), average_cost_before=Decimal("0"),
            source_type="test_receipt", source_document_id=101, source_line_id=1,
            operation_kind="receive_stock", actor_id=1,
        )
        original = InventoryV1StockMovement.objects.create(
            business=self.business, stock=self.stock, movement_type="receipt",
            direction="in", quantity=Decimal("1"), unit="kg", unit_cost=Decimal("9"),
            balance_after=Decimal("5"), average_cost_before=Decimal("3"),
            source_type="test_receipt", source_document_id=102, source_line_id=1,
            operation_kind="receive_stock", actor_id=1,
        )
        barrier = Barrier(2)

        def reverse():
            close_old_connections()
            try:
                use_case = ReverseStockMovementUseCase(
                    DjangoWarehouseRepository(),
                    DjangoIngredientRepository(),
                    DjangoStockRepository(),
                    DjangoStockMovementRepository(),
                    DjangoInventoryUnitOfWork(),
                )
                command = ReverseStockMovementCommand(
                    target=OperationIdentityInput(
                        "test_receipt", original.source_document_id, 1, "receive_stock"
                    ),
                    source=OperationIdentityInput(
                        "test_reversal", 201, 1, "reverse_movement"
                    ),
                    reason="Concurrent correction",
                )
                barrier.wait(timeout=10)
                return use_case.execute(
                    command,
                    InventoryExecutionContext(self.business.pk, actor_id=1),
                )
            except Exception as error:
                return error
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [
                future.result(timeout=25)
                for future in (pool.submit(reverse), pool.submit(reverse))
            ]

        self.assertEqual(sum(not isinstance(result, Exception) for result in results), 1)
        self.assertEqual(
            InventoryV1StockMovement.objects.filter(
                business=self.business, movement_type="reversal",
                reverses_source_document_id=original.source_document_id,
            ).count(),
            1,
        )
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("4.000000000000"))
        self.assertEqual(self.stock.average_cost, Decimal("3"))

    def test_concurrent_operation_creation_with_same_idempotency_key_returns_one_document(self):
        key = uuid4()
        barrier = Barrier(2)

        def create():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return create_operation(
                    business_id=self.business.pk,
                    actor_id=71,
                    operation_type=InventoryOperation.Type.ISSUE,
                    warehouse_id=self.warehouse.pk,
                    reason="Concurrent retry",
                    lines=[{
                        "ingredient_id": self.ingredient.pk,
                        "quantity": Decimal("2"),
                        "unit": "kg",
                    }],
                    idempotency_key=key,
                )
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [
                future.result(timeout=25)
                for future in (pool.submit(create), pool.submit(create))
            ]

        self.assertEqual(results[0].pk, results[1].pk)
        self.assertEqual(
            InventoryOperation.objects.filter(
                business=self.business, idempotency_key=key
            ).count(),
            1,
        )
        self.assertEqual(
            InventoryOperationLine.objects.filter(operation_id=results[0].pk).count(),
            1,
        )

    def test_concurrent_issue_posting_changes_stock_and_ledger_once(self):
        barrier = Barrier(2)

        def post():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return post_issue(
                    business_id=self.business.pk, actor_id=21,
                    operation_id=self.operation.pk,
                )
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(post)
            second = pool.submit(post)
            self.assertEqual(first.result(timeout=20).status, InventoryOperation.Status.POSTED)
            self.assertEqual(second.result(timeout=20).status, InventoryOperation.Status.POSTED)
        self.stock.refresh_from_db()
        self.assertEqual(str(self.stock.quantity), "7.000000000000")
        self.assertEqual(
            InventoryV1StockMovement.objects.filter(
                movement_type="issue", source_document_id=self.operation.pk,
            ).count(),
            1,
        )

    def test_concurrent_distinct_issues_cannot_overspend_one_stock_position(self):
        second = InventoryOperation.objects.create(
            business=self.business, operation_type=InventoryOperation.Type.ISSUE,
            status=InventoryOperation.Status.DRAFT, warehouse=self.warehouse,
            reason="Second issue", created_by_id=1,
        )
        InventoryOperationLine.objects.create(
            operation=second, ingredient=self.ingredient, quantity="7", unit="kg",
        )
        self.operation.lines.update(quantity="7")
        barrier = Barrier(2)

        def post(operation_id):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    post_issue(business_id=self.business.pk, actor_id=22, operation_id=operation_id)
                    return None
                except Exception as error:
                    return error
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [future.result(timeout=20) for future in (
                pool.submit(post, self.operation.pk), pool.submit(post, second.pk),
            )]
        self.assertEqual(sum(result is None for result in results), 1)
        self.assertEqual(sum(isinstance(result, NegativeStock) for result in results), 1)
        self.stock.refresh_from_db()
        self.assertEqual(str(self.stock.quantity), "3.000000000000")
        self.assertEqual(InventoryV1StockMovement.objects.filter(movement_type="issue").count(), 1)

    def test_concurrent_opening_submissions_initialize_a_position_once(self):
        self.stock.quantity = "0"
        self.stock.average_cost = "0"
        self.stock.save(update_fields=("quantity", "average_cost"))
        barrier = Barrier(2)

        def open_stock(reference):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return create_opening_stock(
                    business_id=self.business.pk, actor_id=31,
                    warehouse_id=self.warehouse.pk, reference=reference,
                    lines=[{"ingredient_id": self.ingredient.pk, "quantity": "5", "unit": "kg", "unit_cost": "4"}],
                )
            except Exception as error:
                return error
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [future.result(timeout=20) for future in (
                pool.submit(open_stock, "OPEN-A"), pool.submit(open_stock, "OPEN-B"),
            )]
        self.assertEqual(sum(isinstance(result, InventoryOperation) for result in results), 1)
        self.assertEqual(sum(isinstance(result, OperationConflict) for result in results), 1)
        self.stock.refresh_from_db()
        self.assertEqual(str(self.stock.quantity), "5.000000000000")
        self.assertEqual(InventoryV1StockMovement.objects.filter(movement_type="opening_balance").count(), 1)


    def _wait_for_lock_wait(self, application_name):
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
            Event().wait(0.01)
        self.fail(f"PostgreSQL did not report a lock wait for {application_name}.")

    def test_opening_stock_first_then_issue_uses_committed_opening_balance(self):
        self.stock.quantity = "0"
        self.stock.average_cost = "0"
        self.stock.save(update_fields=("quantity", "average_cost"))
        opening_locked = Event()
        release_opening = Event()
        worker_state = local()
        from inventory.infrastructure.django import operations_service

        original_stock = operations_service._stock

        def hold_opening_after_stock_lock(*args, **kwargs):
            result = original_stock(*args, **kwargs)
            if worker_state.role == "opening":
                opening_locked.set()
                if not release_opening.wait(15):
                    raise TimeoutError("test coordinator did not release opening transaction")
            return result

        def worker(label, role, operation):
            close_old_connections()
            worker_state.role = role
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute("SET application_name = %s", [label])
                return operation(), None
            except Exception as error:
                return None, error
            finally:
                connections.close_all()

        def open_stock():
            return create_opening_stock(
                business_id=self.business.pk,
                actor_id=61,
                warehouse_id=self.warehouse.pk,
                reference="OPEN-BEFORE-ISSUE",
                lines=[{
                    "ingredient_id": self.ingredient.pk,
                    "quantity": "5",
                    "unit": "kg",
                    "unit_cost": "4",
                }],
            )

        def issue_stock():
            return post_issue(
                business_id=self.business.pk,
                actor_id=62,
                operation_id=self.operation.pk,
            )

        prefix = f"opening_first_issue_{self.business.pk}"
        with patch.object(operations_service, "_stock", side_effect=hold_opening_after_stock_lock):
            with ThreadPoolExecutor(max_workers=2) as pool:
                opening_future = pool.submit(worker, f"{prefix}_opening", "opening", open_stock)
                try:
                    self.assertTrue(opening_locked.wait(10), "opening did not lock its Stock row")
                    issue_future = pool.submit(worker, f"{prefix}_issue", "issue", issue_stock)
                    self._wait_for_lock_wait(f"{prefix}_issue")
                finally:
                    release_opening.set()
                opening_result = opening_future.result(timeout=20)
                issue_result = issue_future.result(timeout=20)

        self.assertIsNone(opening_result[1], repr(opening_result[1]))
        self.assertEqual(opening_result[0].status, InventoryOperation.Status.POSTED)
        self.assertIsNone(issue_result[1], repr(issue_result[1]))
        self.assertEqual(issue_result[0].status, InventoryOperation.Status.POSTED)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("2.000000000000"))
        self.assertEqual(
            InventoryV1StockMovement.objects.filter(
                stock=self.stock, movement_type="opening_balance"
            ).count(),
            1,
        )
        self.assertEqual(
            InventoryV1StockMovement.objects.filter(
                stock=self.stock, movement_type="issue"
            ).count(),
            1,
        )

    def test_issue_first_then_opening_stock_rejects_used_position_without_deadlock(self):
        issue_locked = Event()
        release_issue = Event()
        original_save = DjangoStockRepository.save

        def hold_issue_after_stock_lock(repository, stock):
            issue_locked.set()
            if not release_issue.wait(15):
                raise TimeoutError("test coordinator did not release issue transaction")
            return original_save(repository, stock)

        def worker(label, operation):
            close_old_connections()
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute("SET application_name = %s", [label])
                return operation(), None
            except Exception as error:
                return None, error
            finally:
                connections.close_all()

        def issue_stock():
            return post_issue(
                business_id=self.business.pk,
                actor_id=63,
                operation_id=self.operation.pk,
            )

        def open_stock():
            return create_opening_stock(
                business_id=self.business.pk,
                actor_id=64,
                warehouse_id=self.warehouse.pk,
                reference="OPEN-AFTER-ISSUE",
                lines=[{
                    "ingredient_id": self.ingredient.pk,
                    "quantity": "5",
                    "unit": "kg",
                    "unit_cost": "4",
                }],
            )

        prefix = f"issue_first_opening_{self.business.pk}"
        with patch.object(DjangoStockRepository, "save", hold_issue_after_stock_lock):
            with ThreadPoolExecutor(max_workers=2) as pool:
                issue_future = pool.submit(worker, f"{prefix}_issue", issue_stock)
                try:
                    self.assertTrue(issue_locked.wait(10), "issue did not lock its Stock row")
                    opening_future = pool.submit(worker, f"{prefix}_opening", open_stock)
                    self._wait_for_lock_wait(f"{prefix}_opening")
                finally:
                    release_issue.set()
                issue_result = issue_future.result(timeout=20)
                opening_result = opening_future.result(timeout=20)

        self.assertIsNone(issue_result[1], repr(issue_result[1]))
        self.assertEqual(issue_result[0].status, InventoryOperation.Status.POSTED)
        self.assertIsInstance(opening_result[1], OperationConflict)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("7.000000000000"))
        self.assertEqual(
            InventoryV1StockMovement.objects.filter(
                stock=self.stock, movement_type="issue"
            ).count(),
            1,
        )
        self.assertEqual(
            InventoryV1StockMovement.objects.filter(
                stock=self.stock, movement_type="opening_balance"
            ).count(),
            0,
        )


    def test_concurrent_stocktake_approval_and_issue_never_apply_a_stale_count(self):
        stocktake = create_operation(
            business_id=self.business.pk,
            actor_id=41,
            operation_type=InventoryOperation.Type.STOCKTAKE,
            warehouse_id=self.warehouse.pk,
            lines=[{
                "ingredient_id": self.ingredient.pk,
                "quantity": "0",
                "unit": "kg",
                "counted_quantity": "8",
            }],
        )
        barrier = Barrier(2)

        def approve():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return approve_stocktake(
                    business_id=self.business.pk,
                    actor_id=42,
                    operation_id=stocktake.pk,
                )
            except Exception as error:
                return error
            finally:
                connections.close_all()

        def issue():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return post_issue(
                    business_id=self.business.pk,
                    actor_id=43,
                    operation_id=self.operation.pk,
                )
            except Exception as error:
                return error
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            approval_future = pool.submit(approve)
            issue_future = pool.submit(issue)
            approval_result = approval_future.result(timeout=30)
            issue_result = issue_future.result(timeout=30)

        self.assertIsInstance(issue_result, InventoryOperation)
        self.assertEqual(issue_result.status, InventoryOperation.Status.POSTED)
        self.assertEqual(
            isinstance(approval_result, OperationConflict)
            or (
                isinstance(approval_result, InventoryOperation)
                and approval_result.status == InventoryOperation.Status.APPROVED
            ),
            True,
        )

        self.stock.refresh_from_db()
        stocktake.refresh_from_db()
        self.assertIn(
            self.stock.quantity,
            (Decimal("5.000000000000"), Decimal("7.000000000000")),
        )
        if stocktake.status == InventoryOperation.Status.APPROVED:
            self.assertEqual(self.stock.quantity, Decimal("5.000000000000"))
            self.assertEqual(
                InventoryV1StockMovement.objects.filter(
                    source_type="inventory_stocktake",
                    source_document_id=stocktake.pk,
                    movement_type="adjustment",
                ).count(),
                1,
            )
        else:
            self.assertIsInstance(approval_result, OperationConflict)
            self.assertEqual(self.stock.quantity, Decimal("7.000000000000"))
            self.assertEqual(
                InventoryV1StockMovement.objects.filter(
                    source_type="inventory_stocktake",
                    source_document_id=stocktake.pk,
                ).count(),
                0,
            )

        self.assertEqual(
            InventoryV1StockMovement.objects.filter(
                source_type="inventory_issue",
                source_document_id=self.operation.pk,
                movement_type="issue",
            ).count(),
            1,
        )


    def test_concurrent_stocktake_snapshot_and_issue_capture_one_consistent_stock_state(self):
        barrier = Barrier(2)

        def create_stocktake():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return create_operation(
                    business_id=self.business.pk,
                    actor_id=44,
                    operation_type=InventoryOperation.Type.STOCKTAKE,
                    warehouse_id=self.warehouse.pk,
                    lines=[{
                        "ingredient_id": self.ingredient.pk,
                        "quantity": "0",
                        "unit": "kg",
                    }],
                )
            except Exception as error:
                return error
            finally:
                connections.close_all()

        def issue():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return post_issue(
                    business_id=self.business.pk,
                    actor_id=45,
                    operation_id=self.operation.pk,
                )
            except Exception as error:
                return error
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            stocktake_future = pool.submit(create_stocktake)
            issue_future = pool.submit(issue)
            stocktake = stocktake_future.result(timeout=30)
            issue_result = issue_future.result(timeout=30)

        self.assertIsInstance(stocktake, InventoryOperation)
        self.assertIsInstance(issue_result, InventoryOperation)
        self.assertEqual(issue_result.status, InventoryOperation.Status.POSTED)

        line = InventoryOperationLine.objects.get(operation=stocktake)
        movement = InventoryV1StockMovement.objects.get(
            source_type="inventory_issue",
            source_document_id=self.operation.pk,
            movement_type="issue",
        )
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("7.000000000000"))
        self.assertIn(
            line.system_quantity,
            (Decimal("10.000000000000"), Decimal("7.000000000000")),
        )
        if line.system_quantity == Decimal("10.000000000000"):
            self.assertIsNone(line.snapshot_movement_id)
            self.assertEqual(movement.balance_after, Decimal("7.000000000000"))
            update_stocktake_counts(
                business_id=self.business.pk,
                actor_id=46,
                operation_id=stocktake.pk,
                counts={line.pk: {"counted_quantity": Decimal("10")}},
            )
            with self.assertRaises(OperationConflict):
                approve_stocktake(
                    business_id=self.business.pk,
                    actor_id=46,
                    operation_id=stocktake.pk,
                )
        else:
            self.assertEqual(line.snapshot_movement_id, movement.pk)
            update_stocktake_counts(
                business_id=self.business.pk,
                actor_id=46,
                operation_id=stocktake.pk,
                counts={line.pk: {"counted_quantity": Decimal("7")}},
            )
            approved = approve_stocktake(
                business_id=self.business.pk,
                actor_id=46,
                operation_id=stocktake.pk,
            )
            self.assertEqual(approved.status, InventoryOperation.Status.APPROVED)

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("7.000000000000"))


    def test_multiline_issues_lock_stock_positions_in_stable_ingredient_order(self):
        second_ingredient = Ingredient.objects.create(
            business=self.business, name="Sugar", unit="kg"
        )
        second_stock = InventoryV1Stock.objects.create(
            business=self.business, warehouse=self.warehouse,
            ingredient=second_ingredient, unit="kg", quantity="10",
            average_cost="3",
        )

        first_operation = InventoryOperation.objects.create(
            business=self.business, operation_type=InventoryOperation.Type.ISSUE,
            status=InventoryOperation.Status.DRAFT, warehouse=self.warehouse,
            reason="First multi-line issue", created_by_id=51,
        )
        second_operation = InventoryOperation.objects.create(
            business=self.business, operation_type=InventoryOperation.Type.ISSUE,
            status=InventoryOperation.Status.DRAFT, warehouse=self.warehouse,
            reason="Second multi-line issue", created_by_id=52,
        )
        # Persist the lines in opposite orders. The posting path must still
        # acquire the shared Stock projection rows by ascending ingredient ID.
        InventoryOperationLine.objects.create(
            operation=first_operation, ingredient=self.ingredient,
            quantity="1", unit="kg",
        )
        InventoryOperationLine.objects.create(
            operation=first_operation, ingredient=second_ingredient,
            quantity="1", unit="kg",
        )
        InventoryOperationLine.objects.create(
            operation=second_operation, ingredient=second_ingredient,
            quantity="1", unit="kg",
        )
        InventoryOperationLine.objects.create(
            operation=second_operation, ingredient=self.ingredient,
            quantity="1", unit="kg",
        )

        labels = {
            "first": f"inv_lock_order_first_{self.business.pk}",
            "second": f"inv_lock_order_second_{self.business.pk}",
        }
        attempted = {role: Event() for role in labels}
        first_stock_locked = {role: Event() for role in labels}
        release_first_lock = Event()
        worker_state = local()
        from inventory.infrastructure.django import operations_service

        original_stock = operations_service._stock

        def controlled_stock(*args, **kwargs):
            role = worker_state.role
            is_first = worker_state.calls == 0
            worker_state.calls += 1
            if is_first:
                attempted[role].set()
            result = original_stock(*args, **kwargs)
            if is_first:
                first_stock_locked[role].set()
                if not release_first_lock.wait(10):
                    raise TimeoutError("test coordinator did not release first stock lock")
            return result

        def post(operation_id, role):
            close_old_connections()
            worker_state.role = role
            worker_state.calls = 0
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute("SET application_name = %s", [labels[role]])
                result = post_issue(
                    business_id=self.business.pk,
                    actor_id=53,
                    operation_id=operation_id,
                )
                return result, None
            except Exception as error:
                return None, error
            finally:
                connections.close_all()

        second_acquired_a_different_first_lock = False
        second_was_blocked_by_postgres = False
        with patch(
            "inventory.infrastructure.django.operations_service._stock",
            side_effect=controlled_stock,
        ):
            with ThreadPoolExecutor(max_workers=2) as pool:
                first_future = pool.submit(post, first_operation.pk, "first")
                try:
                    self.assertTrue(
                        first_stock_locked["first"].wait(10),
                        "first issue did not lock its first Stock row",
                    )
                    second_future = pool.submit(post, second_operation.pk, "second")
                    self.assertTrue(
                        attempted["second"].wait(10),
                        "second issue did not reach its first Stock lookup",
                    )
                    second_acquired_a_different_first_lock = (
                        first_stock_locked["second"].wait(0.5)
                    )
                    if not second_acquired_a_different_first_lock:
                        deadline = monotonic() + 10
                        while monotonic() < deadline:
                            with connections["default"].cursor() as cursor:
                                cursor.execute(
                                    """SELECT wait_event_type, cardinality(pg_blocking_pids(pid))
                                       FROM pg_stat_activity WHERE application_name = %s""",
                                    [labels["second"]],
                                )
                                wait = cursor.fetchone()
                            if wait and wait[0] == "Lock" and wait[1] > 0:
                                second_was_blocked_by_postgres = True
                                break
                            Event().wait(0.01)
                finally:
                    release_first_lock.set()
                first_result = first_future.result(timeout=30)
                second_result = second_future.result(timeout=30)

        self.assertFalse(
            second_acquired_a_different_first_lock,
            "opposite input line order acquired different first Stock rows",
        )
        self.assertTrue(
            second_was_blocked_by_postgres,
            "second issue did not wait on the first issue's Stock row lock",
        )
        self.assertIsNone(first_result[1], repr(first_result[1]))
        self.assertIsNone(second_result[1], repr(second_result[1]))
        self.assertEqual(first_result[0].status, InventoryOperation.Status.POSTED)
        self.assertEqual(second_result[0].status, InventoryOperation.Status.POSTED)

        self.stock.refresh_from_db()
        second_stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("8.000000000000"))
        self.assertEqual(second_stock.quantity, Decimal("8.000000000000"))
        self.assertEqual(
            InventoryV1StockMovement.objects.filter(
                source_type="inventory_issue",
                source_document_id__in=(first_operation.pk, second_operation.pk),
                movement_type="issue",
            ).count(),
            4,
        )


    def test_concurrent_dispatch_and_receive_apply_transfer_once(self):
        destination = Warehouse.objects.create(
            business=self.business, name="Destination"
        )
        transfer = create_operation(
            business_id=self.business.pk,
            actor_id=61,
            operation_type=InventoryOperation.Type.TRANSFER,
            warehouse_id=self.warehouse.pk,
            destination_warehouse_id=destination.pk,
            lines=[{
                "ingredient_id": self.ingredient.pk,
                "quantity": "3",
                "unit": "kg",
            }],
        )

        def run_concurrently(operation):
            barrier = Barrier(2)

            def invoke():
                close_old_connections()
                try:
                    barrier.wait(timeout=10)
                    return operation(
                        business_id=self.business.pk,
                        actor_id=62,
                        operation_id=transfer.pk,
                    )
                finally:
                    connections.close_all()

            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(invoke), pool.submit(invoke)]
                return [future.result(timeout=30) for future in futures]

        dispatched = run_concurrently(dispatch_transfer)
        self.assertTrue(all(
            result.status == InventoryOperation.Status.IN_TRANSIT
            for result in dispatched
        ))
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("7.000000000000"))
        self.assertEqual(
            InventoryV1StockMovement.objects.filter(
                source_type="inventory_transfer",
                source_document_id=transfer.pk,
                movement_type="transfer_dispatch",
            ).count(),
            1,
        )

        received = run_concurrently(receive_transfer)
        self.assertTrue(all(
            result.status == InventoryOperation.Status.RECEIVED
            for result in received
        ))
        destination_stock = InventoryV1Stock.objects.get(
            business=self.business,
            warehouse=destination,
            ingredient=self.ingredient,
        )
        self.assertEqual(destination_stock.quantity, Decimal("3.000000000000"))
        self.assertEqual(
            InventoryV1StockMovement.objects.filter(
                source_type="inventory_transfer",
                source_document_id=transfer.pk,
                movement_type="transfer_receipt",
            ).count(),
            1,
        )

    def test_concurrent_distinct_transfers_cannot_overspend_source_stock(self):
        destination = Warehouse.objects.create(
            business=self.business, name="Destination"
        )
        second_destination = Warehouse.objects.create(
            business=self.business, name="Second destination"
        )

        def create_transfer(destination_warehouse):
            return create_operation(
                business_id=self.business.pk,
                actor_id=63,
                operation_type=InventoryOperation.Type.TRANSFER,
                warehouse_id=self.warehouse.pk,
                destination_warehouse_id=destination_warehouse.pk,
                lines=[{
                    "ingredient_id": self.ingredient.pk,
                    "quantity": "7",
                    "unit": "kg",
                }],
            )

        first = create_transfer(destination)
        second = create_transfer(second_destination)
        barrier = Barrier(2)

        def dispatch(operation_id):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    return dispatch_transfer(
                        business_id=self.business.pk,
                        actor_id=64,
                        operation_id=operation_id,
                    ), None
                except Exception as error:
                    return None, error
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [
                future.result(timeout=30)
                for future in (
                    pool.submit(dispatch, first.pk),
                    pool.submit(dispatch, second.pk),
                )
            ]

        self.assertEqual(sum(result is not None for result, _ in results), 1)
        self.assertEqual(sum(isinstance(error, NegativeStock) for _, error in results), 1)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("3.000000000000"))
        self.assertEqual(
            InventoryV1StockMovement.objects.filter(
                source_type="inventory_transfer",
                movement_type="transfer_dispatch",
                source_document_id__in=(first.pk, second.pk),
            ).count(),
            1,
        )
        statuses = {
            operation.pk: operation.status
            for operation in InventoryOperation.objects.filter(pk__in=(first.pk, second.pk))
        }
        self.assertEqual(
            sum(status == InventoryOperation.Status.IN_TRANSIT for status in statuses.values()),
            1,
        )
        self.assertEqual(
            sum(status == InventoryOperation.Status.DRAFT for status in statuses.values()),
            1,
        )


    def test_operation_creation_rechecks_item_after_deactivation_wins_reference_lock(self):
        from inventory.infrastructure.django import operations_service
        from inventory.infrastructure.django.master_data_repository import (
            DjangoMasterDataRepository,
        )
        from inventory.application.exceptions import ResourceNotFound

        race_ingredient = Ingredient.objects.create(
            business=self.business, name="Race ingredient", unit="kg"
        )
        lookup_reached_lock = Event()
        allow_lock = Event()
        original_lock = DjangoStockRepository._lock_business_references

        def pause_before_reference_lock(business_id, warehouse_id, ingredient_id, additional_warehouse_ids=()):
            lookup_reached_lock.set()
            if not allow_lock.wait(10):
                raise TimeoutError("test coordinator did not release operation creation")
            return original_lock(
                business_id, warehouse_id, ingredient_id,
                additional_warehouse_ids=additional_warehouse_ids,
            )

        def create():
            close_old_connections()
            try:
                return create_operation(
                    business_id=self.business.pk,
                    actor_id=71,
                    operation_type=InventoryOperation.Type.ISSUE,
                    warehouse_id=self.warehouse.pk,
                    lines=[{"ingredient_id": race_ingredient.pk, "quantity": "1", "unit": "kg"}],
                )
            except Exception as error:
                return error
            finally:
                connections.close_all()

        with patch.object(
            operations_service.DjangoStockRepository,
            "_lock_business_references",
            side_effect=pause_before_reference_lock,
        ):
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(create)
                self.assertTrue(lookup_reached_lock.wait(10))
                updated = DjangoMasterDataRepository().save_item(
                    self.business.pk, race_ingredient.pk, {"is_active": False}
                )
                self.assertFalse(updated.is_active)
                allow_lock.set()
                result = future.result(timeout=20)

        self.assertIsInstance(result, ResourceNotFound)
        self.assertFalse(
            InventoryOperation.objects.filter(
                business=self.business, operation_type=InventoryOperation.Type.ISSUE,
                lines__ingredient=race_ingredient,
            ).exists()
        )

    def test_draft_operation_prevents_item_deactivation(self):
        from inventory.infrastructure.django.master_data_repository import (
            DjangoMasterDataRepository,
        )
        from inventory.application.exceptions import MasterDataConflict

        with self.assertRaises(MasterDataConflict):
            DjangoMasterDataRepository().save_item(
                self.business.pk, self.ingredient.pk, {"is_active": False}
            )

    def test_create_operation_revalidates_warehouse_after_deactivation_wins_reference_lock(self):
        reference_lock_reached = Event()
        release_reference_lock = Event()
        worker_state = local()
        original_lock = DjangoStockRepository._lock_business_references
        race_warehouse = Warehouse.objects.create(business=self.business, name="Race warehouse")

        def pause_before_reference_lock(*args, **kwargs):
            if worker_state.role == "create":
                reference_lock_reached.set()
                if not release_reference_lock.wait(15):
                    raise TimeoutError("test coordinator did not release operation creation")
            return original_lock(*args, **kwargs)

        def create_draft():
            close_old_connections()
            worker_state.role = "create"
            try:
                return create_operation(
                    business_id=self.business.pk,
                    actor_id=71,
                    operation_type=InventoryOperation.Type.ISSUE,
                    warehouse_id=race_warehouse.pk,
                    reason="Race with warehouse deactivation",
                    lines=[{
                        "ingredient_id": self.ingredient.pk,
                        "quantity": "1",
                        "unit": "kg",
                    }],
                ), None
            except Exception as error:
                return None, error
            finally:
                connections.close_all()

        with patch.object(
            DjangoStockRepository,
            "_lock_business_references",
            side_effect=pause_before_reference_lock,
        ):
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(create_draft)
                try:
                    self.assertTrue(
                        reference_lock_reached.wait(10),
                        "operation creation did not reach the reference lock",
                    )
                    DjangoMasterDataRepository().save_warehouse(
                        self.business.pk, race_warehouse.pk, {"is_active": False}
                    )
                finally:
                    release_reference_lock.set()
                result, error = future.result(timeout=20)

        self.assertIsNone(result)
        self.assertIsInstance(error, OperationInputError)
        self.assertFalse(
            InventoryOperation.objects.filter(
                business=self.business,
                reason="Race with warehouse deactivation",
            ).exists()
        )



    def test_replaying_order_consumption_posts_one_issue_and_returns_same_ledger_identity(self):
        from inventory.application.context import InventoryExecutionContext
        from inventory.infrastructure.django.order_consumption_repository import (
            DjangoOrderConsumptionPostingRepository,
        )

        repository = DjangoOrderConsumptionPostingRepository()
        context = InventoryExecutionContext(self.business.pk, actor_id=81)
        kwargs = {
            "warehouse_id": self.warehouse.pk,
            "order_id": 9001,
            "consumption_id": 7001,
            "lines": [{
                "ingredient_id": self.ingredient.pk,
                "quantity": "3",
                "unit": "kg",
            }],
        }

        first = repository.post_order_issue(context, **kwargs)
        replay = repository.post_order_issue(context, **kwargs)

        self.assertEqual(first.operation_id, replay.operation_id)
        self.assertEqual(
            first.movement_ids_by_ingredient,
            replay.movement_ids_by_ingredient,
        )
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("7.000000000000"))
        self.assertEqual(
            InventoryOperation.objects.filter(
                business=self.business,
                notes="OrderInventoryConsumption:7001",
            ).count(),
            1,
        )
        self.assertEqual(
            InventoryV1StockMovement.objects.filter(
                business=self.business,
                source_type="inventory_issue",
                source_document_id=first.operation_id,
                operation_kind="post",
            ).count(),
            1,
        )

    def test_concurrent_cancel_and_issue_posting_allow_only_one_terminal_transition(self):
        barrier = Barrier(2)

        def transition(action):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    if action == "cancel":
                        return cancel_operation(
                            business_id=self.business.pk,
                            operation_type=InventoryOperation.Type.ISSUE,
                            operation_id=self.operation.pk,
                        )
                    return post_issue(
                        business_id=self.business.pk,
                        actor_id=91,
                        operation_id=self.operation.pk,
                    )
                except Exception as error:
                    return error
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = (pool.submit(transition, "cancel"), pool.submit(transition, "post"))
            results = [future.result(timeout=25) for future in futures]

        successes = [result for result in results if not isinstance(result, Exception)]
        conflicts = [result for result in results if isinstance(result, OperationConflict)]
        self.assertEqual(len(successes), 1)
        self.assertEqual(len(conflicts), 1)

        self.operation.refresh_from_db()
        movements = InventoryV1StockMovement.objects.filter(
            business=self.business,
            movement_type="issue",
            source_document_id=self.operation.pk,
        )
        if self.operation.status == InventoryOperation.Status.CANCELLED:
            self.assertEqual(movements.count(), 0)
            self.stock.refresh_from_db()
            self.assertEqual(self.stock.quantity, Decimal("10"))
        else:
            self.assertEqual(self.operation.status, InventoryOperation.Status.POSTED)
            self.assertEqual(movements.count(), 1)
            self.stock.refresh_from_db()
            self.assertEqual(self.stock.quantity, Decimal("7.000000000000"))

    def test_concurrent_cancel_and_transfer_dispatch_allow_only_one_transition(self):
        destination = Warehouse.objects.create(
            business=self.business, name="Transfer destination"
        )
        transfer = create_operation(
            business_id=self.business.pk,
            actor_id=92,
            operation_type=InventoryOperation.Type.TRANSFER,
            warehouse_id=self.warehouse.pk,
            destination_warehouse_id=destination.pk,
            reason="Race cancellation against dispatch",
            lines=[{
                "ingredient_id": self.ingredient.pk,
                "quantity": "3",
                "unit": "kg",
            }],
        )
        barrier = Barrier(2)

        def transition(action):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    if action == "cancel":
                        return cancel_operation(
                            business_id=self.business.pk,
                            operation_type=InventoryOperation.Type.TRANSFER,
                            operation_id=transfer.pk,
                        )
                    return dispatch_transfer(
                        business_id=self.business.pk,
                        actor_id=93,
                        operation_id=transfer.pk,
                    )
                except Exception as error:
                    return error
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = (
                pool.submit(transition, "cancel"),
                pool.submit(transition, "dispatch"),
            )
            results = [future.result(timeout=25) for future in futures]

        successes = [result for result in results if not isinstance(result, Exception)]
        conflicts = [result for result in results if isinstance(result, OperationConflict)]
        self.assertEqual(len(successes), 1)
        self.assertEqual(len(conflicts), 1)

        transfer.refresh_from_db()
        movements = InventoryV1StockMovement.objects.filter(
            business=self.business,
            source_type="inventory_transfer",
            source_document_id=transfer.pk,
            movement_type="transfer_dispatch",
        )
        if transfer.status == InventoryOperation.Status.CANCELLED:
            self.assertEqual(movements.count(), 0)
            self.stock.refresh_from_db()
            self.assertEqual(self.stock.quantity, Decimal("10"))
            self.assertFalse(
                InventoryV1Stock.objects.filter(
                    business=self.business,
                    warehouse=destination,
                    ingredient=self.ingredient,
                ).exists()
            )
        else:
            self.assertEqual(transfer.status, InventoryOperation.Status.IN_TRANSIT)
            self.assertEqual(movements.count(), 1)
            self.stock.refresh_from_db()
            self.assertEqual(self.stock.quantity, Decimal("7.000000000000"))
            self.assertFalse(
                InventoryV1Stock.objects.filter(
                    business=self.business,
                    warehouse=destination,
                    ingredient=self.ingredient,
                ).exists()
            )


    def test_issue_and_transfer_dispatch_serialize_on_shared_source_stock(self):
        from inventory.infrastructure.django import operations_service

        worker_state = local()
        original_stock = operations_service._stock
        prefix = f"issue_transfer_race_{self.business.pk}_{uuid4().hex[:6]}"

        def hold_winner_after_stock_lock(*args, **kwargs):
            result = original_stock(*args, **kwargs)
            if (
                worker_state.role == worker_state.winner
                and not getattr(worker_state, "held", False)
            ):
                worker_state.held = True
                locked.set()
                if not release.wait(15):
                    raise TimeoutError("test coordinator did not release outbound stock lock")
            return result

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
                Event().wait(0.01)
            self.fail(f"PostgreSQL did not report a lock wait for {application_name}.")

        def run_worker(role, winner, label, operation):
            close_old_connections()
            worker_state.role = role
            worker_state.winner = winner
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute("SET application_name = %s", [label])
                try:
                    return operation(), None
                except Exception as error:
                    return None, error
            finally:
                connections.close_all()

        for winner in ("issue", "transfer"):
            with self.subTest(winner=winner):
                self.stock.quantity = Decimal("10")
                self.stock.average_cost = Decimal("4")
                self.stock.save(update_fields=("quantity", "average_cost"))

                destination = Warehouse.objects.create(
                    business=self.business,
                    name=f"Destination {winner}",
                )
                issue = create_operation(
                    business_id=self.business.pk,
                    actor_id=81,
                    operation_type=InventoryOperation.Type.ISSUE,
                    warehouse_id=self.warehouse.pk,
                    reason=f"Issue competing with {winner}",
                    lines=[{
                        "ingredient_id": self.ingredient.pk,
                        "quantity": "7",
                        "unit": "kg",
                    }],
                )
                transfer = create_operation(
                    business_id=self.business.pk,
                    actor_id=82,
                    operation_type=InventoryOperation.Type.TRANSFER,
                    warehouse_id=self.warehouse.pk,
                    destination_warehouse_id=destination.pk,
                    reason=f"Transfer competing with {winner}",
                    lines=[{
                        "ingredient_id": self.ingredient.pk,
                        "quantity": "7",
                        "unit": "kg",
                    }],
                )

                locked = Event()
                release = Event()
                worker_state.held = False
                winner_label = f"{prefix}_{winner}"
                loser = "transfer" if winner == "issue" else "issue"
                loser_label = f"{prefix}_{loser}"

                def post_issue_winner():
                    return post_issue(
                        business_id=self.business.pk,
                        actor_id=83,
                        operation_id=issue.pk,
                    )

                def dispatch_winner():
                    return dispatch_transfer(
                        business_id=self.business.pk,
                        actor_id=84,
                        operation_id=transfer.pk,
                    )

                operations = {
                    "issue": post_issue_winner,
                    "transfer": dispatch_winner,
                }

                with patch.object(
                    operations_service,
                    "_stock",
                    side_effect=hold_winner_after_stock_lock,
                ):
                    with ThreadPoolExecutor(max_workers=2) as pool:
                        winner_future = pool.submit(
                            run_worker,
                            winner,
                            winner,
                            winner_label,
                            operations[winner],
                        )
                        try:
                            self.assertTrue(
                                locked.wait(10),
                                f"{winner} did not acquire the shared source stock lock",
                            )
                            loser_future = pool.submit(
                                run_worker,
                                loser,
                                winner,
                                loser_label,
                                operations[loser],
                            )
                            wait_until_blocked(loser_label)
                        finally:
                            release.set()
                        winner_result = winner_future.result(timeout=20)
                        loser_result = loser_future.result(timeout=20)

                self.assertIsNone(winner_result[1], repr(winner_result[1]))
                self.assertIsInstance(loser_result[1], NegativeStock)
                self.stock.refresh_from_db()
                self.assertEqual(self.stock.quantity, Decimal("3.000000000000"))

                issue.refresh_from_db()
                transfer.refresh_from_db()
                if winner == "issue":
                    self.assertEqual(issue.status, InventoryOperation.Status.POSTED)
                    self.assertEqual(transfer.status, InventoryOperation.Status.DRAFT)
                else:
                    self.assertEqual(transfer.status, InventoryOperation.Status.IN_TRANSIT)
                    self.assertEqual(issue.status, InventoryOperation.Status.DRAFT)

                outbound = InventoryV1StockMovement.objects.filter(
                    stock=self.stock,
                    source_document_id__in=(issue.pk, transfer.pk),
                    movement_type__in=("issue", "transfer_dispatch"),
                )
                self.assertEqual(outbound.count(), 1)
