from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase, skipUnlessDBFeature

from accounts.models import Business
from inventory.infrastructure.django.models import (
    InventoryOperation, InventoryOperationLine, InventoryV1Stock,
    InventoryV1StockMovement,
)
from inventory.infrastructure.django.operations_service import post_issue
from inventory.infrastructure.django.operations_service import create_opening_stock
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
