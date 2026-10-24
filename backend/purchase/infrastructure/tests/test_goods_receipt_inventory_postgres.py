from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from decimal import Decimal
from threading import Barrier
from unittest import skipUnless
from uuid import uuid4

from django.db import connection, connections
from django.test import TransactionTestCase

from accounts.models import Business, User
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
from inventory.models import Ingredient, Warehouse
from inventory.application.use_cases.receive_stock import ReceiveStockUseCase
from purchase.application.dto.goods_receipt import (
    CreateGoodsReceiptDTO,
    CreateGoodsReceiptItemDTO,
)
from purchase.application.exceptions import PurchaseInventoryIntegrationError
from purchase.application.exceptions import GoodsReceiptIdempotencyPayloadMismatch
from purchase.application.use_cases.goods_receipt.create_goods_receipt import (
    CreateGoodsReceiptUseCase,
)
from purchase.domain.enums.purchase_unit import PurchaseUnit
from purchase.infrastructure.persistence.django.repositories.goods_receipt_repository import (
    DjangoGoodsReceiptRepository,
)
from purchase.infrastructure.persistence.django.repositories.purchase_order_line_reader import (
    DjangoPurchaseOrderLineReader,
)
from purchase.infrastructure.persistence.django.repositories.purchase_order_repository import (
    DjangoPurchaseOrderRepository,
)
from purchase.infrastructure.persistence.transaction import DjangoTransactionManager
from purchase.infrastructure.services.inventory_receipt_gateway import (
    DjangoInventoryReceiptGateway,
)
from purchase.models import (
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
)


@skipUnless(
    connection.vendor == "postgresql",
    "Purchase + Inventory atomicity verification requires PostgreSQL.",
)
class GoodsReceiptInventoryPostgreSQLTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self) -> None:
        self.business = Business.objects.create(name="Inventory integration", slug="inventory-integration")
        self.user = User.objects.create_user(
            email="inventory-integration@example.com",
            password="test-only",
            name="Inventory Integration",
        )
        self.supplier = Supplier.objects.create(
            business=self.business,
            name="Supplier",
        )
        self.ingredient = Ingredient.objects.create(
            business=self.business,
            name="Flour",
            unit=Ingredient.Unit.KG,
        )
        self.warehouse = Warehouse.objects.create(
            business=self.business,
            name="Main",
            is_default=True,
        )
        self.order = PurchaseOrder.objects.create(
            business=self.business,
            supplier=self.supplier,
            order_date=date(2026, 10, 1),
            status=PurchaseOrder.Status.SENT,
        )

    def _item(self, *, unit: str, quantity: str = "1000", price: str = "150"):
        return PurchaseOrderItem.objects.create(
            purchase_order=self.order,
            ingredient=self.ingredient,
            quantity=Decimal(quantity),
            unit_price=Decimal(price),
            purchase_unit=unit,
        )

    def _use_case(self) -> CreateGoodsReceiptUseCase:
        return self._use_case_with_repository(DjangoGoodsReceiptRepository())

    def _use_case_with_repository(self, receipt_repository) -> CreateGoodsReceiptUseCase:
        inventory = ReceiveStockUseCase(
            DjangoWarehouseRepository(),
            DjangoIngredientRepository(),
            DjangoStockRepository(),
            DjangoStockMovementRepository(),
            DjangoInventoryUnitOfWork(),
        )
        return CreateGoodsReceiptUseCase(
            receipt_repository,
            DjangoPurchaseOrderRepository(),
            DjangoPurchaseOrderLineReader(),
            DjangoInventoryReceiptGateway(inventory),
            DjangoTransactionManager(),
        )

    def _command(
        self,
        item: PurchaseOrderItem,
        *,
        unit: PurchaseUnit,
        key=None,
        quantity: str = "500",
        order: PurchaseOrder | None = None,
    ) -> CreateGoodsReceiptDTO:
        return CreateGoodsReceiptDTO(
            business_id=self.business.id,
            purchase_order_id=(order or self.order).id,
            received_by_id=self.user.id,
            received_date=datetime(2026, 10, 2, 12),
            idempotency_key=key or uuid4(),
            items=[
                CreateGoodsReceiptItemDTO(
                    purchase_order_item_id=item.id,
                    received_quantity=Decimal(quantity),
                    purchase_unit=unit,
                )
            ],
        )

    def _run_concurrently(self, workers):
        barrier = Barrier(len(workers))

        def run(worker):
            connections.close_all()
            try:
                barrier.wait(timeout=15)
                return worker()
            except Exception as error:
                return error
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=len(workers)) as executor:
            futures = [executor.submit(run, worker) for worker in workers]
            return [future.result(timeout=30) for future in futures]

    def test_receipt_and_inventory_movement_commit_atomically(self) -> None:
        item = self._item(unit="g")

        result = self._use_case().execute(self._command(item, unit=PurchaseUnit.G))
        receipt = result.receipt

        stock = InventoryV1Stock.objects.get(
            business=self.business,
            warehouse=self.warehouse,
            ingredient=self.ingredient,
        )
        movement = InventoryV1StockMovement.objects.get()
        self.assertEqual(receipt.items[0].id, movement.source_line_id)
        self.assertEqual(receipt.id, movement.source_document_id)
        self.assertEqual(movement.source_type, "goods_receipt")
        self.assertEqual(stock.quantity, Decimal("0.500000000000"))
        self.assertEqual(stock.average_cost, Decimal("150000"))
        self.assertEqual(movement.actor_id, self.user.id)

    def test_inventory_failure_rolls_back_goods_receipt_and_purchase_state(self) -> None:
        item = self._item(unit="l")
        key = uuid4()

        with self.assertRaises(PurchaseInventoryIntegrationError):
            self._use_case().execute(
                self._command(item, unit=PurchaseUnit.L, key=key)
            )

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, PurchaseOrder.Status.SENT)
        self.assertFalse(self.order.receipts.exists())
        self.assertEqual(GoodsReceiptItem.objects.count(), 0)
        self.assertEqual(InventoryV1Stock.objects.count(), 0)
        self.assertEqual(InventoryV1StockMovement.objects.count(), 0)

        item.purchase_unit = "kg"
        item.save(update_fields=["purchase_unit", "updated_at"])
        retry = self._use_case().execute(
            self._command(item, unit=PurchaseUnit.KG, key=key)
        )
        self.assertFalse(retry.replayed)
        self.assertEqual(self.order.receipts.count(), 1)
        self.assertEqual(InventoryV1StockMovement.objects.count(), 1)

    def test_concurrent_same_key_same_payload_creates_one_receipt_and_movement(self) -> None:
        item = self._item(unit="g")
        key = uuid4()
        command = self._command(item, unit=PurchaseUnit.G, key=key)
        results = self._run_concurrently([
            lambda: self._use_case().execute(command),
            lambda: self._use_case().execute(command),
        ])

        self.assertFalse(any(isinstance(result, Exception) for result in results))
        self.assertEqual(sum(result.replayed for result in results), 1)
        self.assertEqual(results[0].receipt.id, results[1].receipt.id)
        self.assertEqual(self.order.receipts.count(), 1)
        self.assertEqual(GoodsReceiptItem.objects.count(), 1)
        self.assertEqual(InventoryV1StockMovement.objects.count(), 1)

    def test_concurrent_same_key_different_payload_conflicts_without_duplicate_posting(self) -> None:
        item = self._item(unit="g")
        key = uuid4()
        results = self._run_concurrently([
            lambda: self._use_case().execute(
                self._command(item, unit=PurchaseUnit.G, key=key, quantity="400")
            ),
            lambda: self._use_case().execute(
                self._command(item, unit=PurchaseUnit.G, key=key, quantity="500")
            ),
        ])

        self.assertEqual(sum(not isinstance(result, Exception) for result in results), 1)
        self.assertEqual(
            sum(isinstance(result, GoodsReceiptIdempotencyPayloadMismatch) for result in results),
            1,
        )
        self.assertEqual(self.order.receipts.count(), 1)
        self.assertEqual(GoodsReceiptItem.objects.count(), 1)
        self.assertEqual(InventoryV1StockMovement.objects.count(), 1)

    def test_concurrent_key_claim_race_across_orders_recovers_winner_after_rollback(self) -> None:
        first_item = self._item(unit="g")
        other_order = PurchaseOrder.objects.create(
            business=self.business,
            supplier=self.supplier,
            order_date=date(2026, 10, 1),
            status=PurchaseOrder.Status.SENT,
        )
        second_item = PurchaseOrderItem.objects.create(
            purchase_order=other_order,
            ingredient=self.ingredient,
            quantity=Decimal("1000"),
            unit_price=Decimal("150"),
            purchase_unit="g",
        )
        key = uuid4()
        insert_barrier = Barrier(2)

        class BarrierRepository(DjangoGoodsReceiptRepository):
            def save(inner_self, receipt):
                insert_barrier.wait(timeout=15)
                return super(BarrierRepository, inner_self).save(receipt)

        def execute(item, order, quantity):
            return self._use_case_with_repository(BarrierRepository()).execute(
                self._command(
                    item,
                    unit=PurchaseUnit.G,
                    key=key,
                    quantity=quantity,
                    order=order,
                )
            )

        results = self._run_concurrently([
            lambda: execute(first_item, self.order, "400"),
            lambda: execute(second_item, other_order, "500"),
        ])

        self.assertEqual(sum(not isinstance(result, Exception) for result in results), 1)
        self.assertEqual(
            sum(isinstance(result, GoodsReceiptIdempotencyPayloadMismatch) for result in results),
            1,
        )
        self.assertEqual(GoodsReceipt.objects.filter(business=self.business).count(), 1)
        self.assertEqual(GoodsReceiptItem.objects.count(), 1)
        self.assertEqual(InventoryV1StockMovement.objects.count(), 1)
