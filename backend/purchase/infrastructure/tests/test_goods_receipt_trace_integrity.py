import json
from datetime import date, datetime
from decimal import Decimal
from io import StringIO
from unittest import skipUnless
from uuid import uuid4

from django.core.management import call_command
from django.db import DatabaseError, connection, transaction
from django.db.models.deletion import ProtectedError
from django.test import TransactionTestCase

from accounts.models import Business, User
from inventory.application.use_cases.receive_stock import ReceiveStockUseCase
from inventory.infrastructure.django.models import InventoryV1StockMovement
from inventory.infrastructure.django.repositories import (
    DjangoIngredientRepository,
    DjangoStockMovementRepository,
    DjangoStockRepository,
    DjangoWarehouseRepository,
)
from inventory.infrastructure.django.unit_of_work import DjangoInventoryUnitOfWork
from inventory.models import Ingredient, Warehouse
from purchase.application.dto.goods_receipt import (
    CreateGoodsReceiptDTO,
    CreateGoodsReceiptItemDTO,
)
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
    GoodsReceiptInventoryMovementLink,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
)


class GoodsReceiptTraceFixtureMixin:
    def setUp(self):
        self.business = Business.objects.create(
            name="Receipt audit",
            slug="receipt-audit",
        )
        self.user = User.objects.create_user(
            email="receipt-audit@example.com",
            password="test-only",
            name="Receipt Audit",
        )
        self.supplier = Supplier.objects.create(
            business=self.business,
            name="Audit Supplier",
        )
        self.ingredient = Ingredient.objects.create(
            business=self.business,
            name="Audit Flour",
            unit=Ingredient.Unit.KG,
        )
        self.warehouse = Warehouse.objects.create(
            business=self.business,
            name="Audit Warehouse",
            is_default=True,
        )
        self.order = PurchaseOrder.objects.create(
            business=self.business,
            supplier=self.supplier,
            order_date=date(2026, 10, 1),
            status=PurchaseOrder.Status.SENT,
        )
        self.order_item = PurchaseOrderItem.objects.create(
            purchase_order=self.order,
            ingredient=self.ingredient,
            quantity=Decimal("10"),
            unit_price=Decimal("150"),
            purchase_unit="kg",
        )

    def _create_received_item_without_movement(self):
        receipt = GoodsReceipt.objects.create(
            business=self.business,
            purchase_order=self.order,
            received_by=self.user,
            received_date=datetime(2026, 10, 2, 12),
        )
        return GoodsReceiptItem.objects.create(
            receipt=receipt,
            purchase_order_item=self.order_item,
            received_quantity=Decimal("1"),
            rejected_quantity=Decimal("0"),
            purchase_unit="kg",
        )

    def _receive(self):
        inventory = ReceiveStockUseCase(
            DjangoWarehouseRepository(),
            DjangoIngredientRepository(),
            DjangoStockRepository(),
            DjangoStockMovementRepository(),
            DjangoInventoryUnitOfWork(),
        )
        use_case = CreateGoodsReceiptUseCase(
            DjangoGoodsReceiptRepository(),
            DjangoPurchaseOrderRepository(),
            DjangoPurchaseOrderLineReader(),
            DjangoInventoryReceiptGateway(inventory),
            DjangoTransactionManager(),
        )
        return use_case.execute(
            CreateGoodsReceiptDTO(
                business_id=self.business.id,
                purchase_order_id=self.order.id,
                received_by_id=self.user.id,
                received_date=datetime(2026, 10, 2, 12),
                idempotency_key=uuid4(),
                items=[
                    CreateGoodsReceiptItemDTO(
                        purchase_order_item_id=self.order_item.id,
                        received_quantity=Decimal("1"),
                        purchase_unit=PurchaseUnit.KG,
                    )
                ],
            )
        )


class GoodsReceiptTraceAuditTests(GoodsReceiptTraceFixtureMixin, TransactionTestCase):
    reset_sequences = True

    def test_audit_reports_received_item_without_inventory_movement(self):
        item = self._create_received_item_without_movement()
        output = StringIO()

        call_command(
            "audit_goods_receipt_inventory_trace",
            business_id=self.business.id,
            stdout=output,
        )

        report = json.loads(output.getvalue())
        self.assertEqual(report["issue_count"], 1)
        self.assertEqual(
            report["issues"][0]["code"],
            "receipt_item_without_movement",
        )
        self.assertEqual(report["issues"][0]["receipt_item_id"], item.id)

    def test_audit_reports_clean_linked_receipt(self):
        self._receive()
        output = StringIO()

        call_command(
            "audit_goods_receipt_inventory_trace",
            business_id=self.business.id,
            stdout=output,
        )

        report = json.loads(output.getvalue())
        self.assertEqual(report["issue_count"], 0)
        self.assertEqual(report["checked"]["goods_receipt_movements"], 1)
        self.assertEqual(report["checked"]["received_receipt_items"], 1)
        self.assertEqual(report["checked"]["links"], 1)


@skipUnless(
    connection.vendor == "postgresql",
    "Database-level historical immutability guards require PostgreSQL.",
)
class GoodsReceiptHistoricalIntegrityPostgreSQLTests(
    GoodsReceiptTraceFixtureMixin,
    TransactionTestCase,
):
    reset_sequences = True

    def _linked_records(self):
        result = self._receive()
        receipt = GoodsReceipt.objects.get(pk=result.receipt.id)
        item = receipt.items.get()
        link = GoodsReceiptInventoryMovementLink.objects.get(receipt_item=item)
        movement = InventoryV1StockMovement.objects.get(pk=link.movement_id)
        return receipt, item, link, movement

    def test_receipt_and_item_updates_are_rejected_by_database(self):
        receipt, item, _, _ = self._linked_records()

        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                GoodsReceipt.objects.filter(pk=receipt.pk).update(notes="rewritten")

        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                GoodsReceiptItem.objects.filter(pk=item.pk).update(
                    received_quantity=Decimal("2")
                )

    def test_orm_delete_is_protected_and_raw_delete_is_rejected(self):
        receipt, item, _, _ = self._linked_records()

        with self.assertRaises(ProtectedError):
            receipt.delete()

        with self.assertRaises(ProtectedError):
            item.delete()

        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM purchase_goodsreceiptitem WHERE id = %s",
                        [item.pk],
                    )

        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM purchase_goodsreceipt WHERE id = %s",
                        [receipt.pk],
                    )

    def test_link_and_receipt_movement_are_immutable(self):
        _, _, link, movement = self._linked_records()

        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                GoodsReceiptInventoryMovementLink.objects.filter(
                    pk=link.pk
                ).update(movement_id=movement.pk + 100)

        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                GoodsReceiptInventoryMovementLink.objects.filter(
                    pk=link.pk
                ).delete()

        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                InventoryV1StockMovement.objects.filter(
                    pk=movement.pk
                ).update(reason="rewritten historical reason")

        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM inventory_v1_stock_movement WHERE id = %s",
                        [movement.pk],
                    )
