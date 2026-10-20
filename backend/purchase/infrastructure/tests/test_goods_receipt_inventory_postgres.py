from datetime import date, datetime
from decimal import Decimal
from unittest import skipUnless

from django.db import connection
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
        inventory = ReceiveStockUseCase(
            DjangoWarehouseRepository(),
            DjangoIngredientRepository(),
            DjangoStockRepository(),
            DjangoStockMovementRepository(),
            DjangoInventoryUnitOfWork(),
        )
        return CreateGoodsReceiptUseCase(
            DjangoGoodsReceiptRepository(),
            DjangoPurchaseOrderRepository(),
            DjangoPurchaseOrderLineReader(),
            DjangoInventoryReceiptGateway(inventory),
            DjangoTransactionManager(),
        )

    def _command(self, item: PurchaseOrderItem, *, unit: PurchaseUnit) -> CreateGoodsReceiptDTO:
        return CreateGoodsReceiptDTO(
            business_id=self.business.id,
            purchase_order_id=self.order.id,
            received_by_id=self.user.id,
            received_date=datetime(2026, 10, 2, 12),
            items=[
                CreateGoodsReceiptItemDTO(
                    purchase_order_item_id=item.id,
                    received_quantity=Decimal("500"),
                    purchase_unit=unit,
                )
            ],
        )

    def test_receipt_and_inventory_movement_commit_atomically(self) -> None:
        item = self._item(unit="g")

        receipt = self._use_case().execute(self._command(item, unit=PurchaseUnit.G))

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

        with self.assertRaises(PurchaseInventoryIntegrationError):
            self._use_case().execute(self._command(item, unit=PurchaseUnit.L))

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, PurchaseOrder.Status.SENT)
        self.assertFalse(self.order.receipts.exists())
        self.assertEqual(GoodsReceiptItem.objects.count(), 0)
        self.assertEqual(InventoryV1Stock.objects.count(), 0)
        self.assertEqual(InventoryV1StockMovement.objects.count(), 0)
