from decimal import Decimal
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
from inventory.infrastructure.django.operations_service import (
    approve_stocktake,
    create_opening_stock,
    create_operation,
    post_issue,
    update_stocktake_counts,
)
from inventory.application.exceptions import OperationConflict
from inventory.models import Ingredient, Warehouse
from inventory.domain.exceptions import NegativeStock


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
