from datetime import datetime
from decimal import Decimal
import inspect

from django.db import transaction
from django.test import TestCase

from accounts.models import Business, User
from inventory.models import Ingredient, Stock, StockTransaction, Warehouse
from purchase.domain.entities.goods_receipt import GoodsReceipt, GoodsReceiptItem
from purchase.infrastructure.persistence.django.mappers import GoodsReceiptMapper
from purchase.infrastructure.persistence.django.repositories.goods_receipt_repository import (
    DjangoGoodsReceiptRepository,
)
from purchase.infrastructure.persistence.django.repositories.purchase_order_line_reader import (
    DjangoPurchaseOrderLineReader,
)
from purchase.infrastructure.persistence.django.repositories.purchase_order_repository import (
    DjangoPurchaseOrderRepository,
)
from purchase.infrastructure.services.stock_transaction_gateway import (
    DjangoStockTransactionGateway,
)
from purchase.models import (
    GoodsReceipt as DjangoGoodsReceipt,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
)
from purchase.application.ports.goods_receipt import StockInRequest


class GoodsReceiptInfrastructureTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.business = Business.objects.create(name="Business", slug="business")
        cls.other_business = Business.objects.create(
            name="Other Business",
            slug="other-business",
        )
        cls.user = User.objects.create_user(
            email="receiver@example.com",
            password="password",
            name="Receiver",
        )
        cls.ingredient = Ingredient.objects.create(
            business=cls.business,
            name="Flour",
            unit=Ingredient.Unit.KG,
        )
        cls.other_ingredient = Ingredient.objects.create(
            business=cls.other_business,
            name="Other Flour",
            unit=Ingredient.Unit.KG,
        )
        cls.warehouse = Warehouse.objects.create(
            business=cls.business,
            name="Main",
            is_default=True,
        )
        cls.supplier = Supplier.objects.create(
            business=cls.business,
            name="Supplier",
        )
        cls.purchase_order = PurchaseOrder.objects.create(
            business=cls.business,
            supplier=cls.supplier,
            order_date=datetime(2026, 9, 8).date(),
            status=PurchaseOrder.Status.SENT,
        )
        cls.purchase_order_item = PurchaseOrderItem.objects.create(
            purchase_order=cls.purchase_order,
            ingredient=cls.ingredient,
            quantity=Decimal("10"),
            unit_price=Decimal("500.00"),
        )

    def receipt(self, quantity="4", rejected="0"):
        return GoodsReceipt(
            id=None,
            business_id=self.business.id,
            purchase_order_id=self.purchase_order.id,
            received_by_id=self.user.id,
            received_date=datetime(2026, 9, 8, 12),
            items=[GoodsReceiptItem(
                self.purchase_order_item.id,
                Decimal(quantity),
                Decimal(rejected),
            )],
        )

    def test_repository_persists_and_loads_scoped_aggregate(self):
        repository = DjangoGoodsReceiptRepository()
        saved = repository.save(self.receipt())

        loaded = repository.get_by_id_for_business(
            saved.id,
            self.business.id,
        )

        self.assertEqual(loaded.business_id, self.business.id)
        self.assertEqual(loaded.items[0].received_quantity, Decimal("4"))
        self.assertIsNone(
            repository.get_by_id_for_business(saved.id, self.other_business.id)
        )

    def test_for_update_loader_locks_only_tenant_scoped_po_root(self):
        repository = DjangoPurchaseOrderRepository()
        source = inspect.getsource(
            DjangoPurchaseOrderRepository.get_by_id_for_business_for_update
        )
        self.assertIn('select_for_update(of=("self",))', source)
        self.assertIn("business_id=business_id", source)
        self.assertLess(source.index("select_for_update"), source.index("self._aggregate_queryset()"))

        with transaction.atomic():
            locked = repository.get_by_id_for_business_for_update(
                self.purchase_order.id,
                self.business.id,
            )
            self.assertEqual(locked.id, self.purchase_order.id)
            self.assertIsNone(repository.get_by_id_for_business_for_update(
                self.purchase_order.id,
                self.other_business.id,
            ))

    def test_existing_goods_receipt_cannot_be_updated(self):
        repository = DjangoGoodsReceiptRepository()
        saved = repository.save(self.receipt())
        saved.items[0].received_quantity = Decimal("5")
        with self.assertRaisesRegex(ValueError, "immutable"):
            repository.save(saved)

    def test_received_quantity_query_excludes_rejected_quantity(self):
        repository = DjangoGoodsReceiptRepository()
        repository.save(self.receipt(quantity="4", rejected="3"))

        quantities = repository.received_quantities_for_purchase_order(
            self.business.id,
            self.purchase_order.id,
        )

        self.assertEqual(
            quantities[self.purchase_order_item.id],
            Decimal("4"),
        )

    def test_line_reader_is_scoped_to_order_and_business(self):
        lines = DjangoPurchaseOrderLineReader().get_lines(
            self.purchase_order.id,
            self.business.id,
        )

        self.assertEqual(
            lines[self.purchase_order_item.id].ingredient_id,
            self.ingredient.id,
        )
        self.assertEqual(
            lines[self.purchase_order_item.id].ordered_quantity,
            Decimal("10"),
        )
        self.assertEqual(
            DjangoPurchaseOrderLineReader().get_lines(
                self.purchase_order.id,
                self.other_business.id,
            ),
            {},
        )

    def test_stock_gateway_creates_stock_for_received_quantity_only(self):
        DjangoStockTransactionGateway().create_stock_in(StockInRequest(
            business_id=self.business.id,
            purchase_order_id=self.purchase_order.id,
            goods_receipt_id=1,
            purchase_order_item_id=self.purchase_order_item.id,
            ingredient_id=self.ingredient.id,
            quantity=Decimal("4"),
        ))

        stock = Stock.objects.get(
            warehouse=self.warehouse,
            ingredient=self.ingredient,
        )
        self.assertEqual(stock.quantity, Decimal("4"))
        transaction = StockTransaction.objects.get(stock=stock)
        self.assertEqual(transaction.type, StockTransaction.Type.PURCHASE_RECEIVE)
        self.assertEqual(transaction.reference_type, "goods_receipt")
        self.assertEqual(transaction.unit_cost, Decimal("500.00"))

    def test_stock_transactions_use_each_purchase_order_item_unit_price(self):
        other_item = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            ingredient=self.ingredient,
            quantity=Decimal("2"),
            unit_price=Decimal("750.00"),
        )
        gateway = DjangoStockTransactionGateway()

        gateway.create_stock_in(StockInRequest(
            business_id=self.business.id,
            purchase_order_id=self.purchase_order.id,
            goods_receipt_id=1,
            purchase_order_item_id=self.purchase_order_item.id,
            ingredient_id=self.ingredient.id,
            quantity=Decimal("1"),
        ))
        gateway.create_stock_in(StockInRequest(
            business_id=self.business.id,
            purchase_order_id=self.purchase_order.id,
            goods_receipt_id=1,
            purchase_order_item_id=other_item.id,
            ingredient_id=self.ingredient.id,
            quantity=Decimal("1"),
        ))

        self.assertEqual(
            list(
                StockTransaction.objects.order_by("id").values_list(
                    "unit_cost",
                    flat=True,
                )
            ),
            [Decimal("500.00"), Decimal("750.00")],
        )

    def test_purchase_order_discount_and_tax_do_not_change_unit_cost(self):
        self.purchase_order.discount = Decimal("100")
        self.purchase_order.tax = Decimal("50")
        self.purchase_order.save(update_fields=["discount", "tax", "updated_at"])

        DjangoStockTransactionGateway().create_stock_in(StockInRequest(
            business_id=self.business.id,
            purchase_order_id=self.purchase_order.id,
            goods_receipt_id=1,
            purchase_order_item_id=self.purchase_order_item.id,
            ingredient_id=self.ingredient.id,
            quantity=Decimal("1"),
        ))

        self.assertEqual(
            StockTransaction.objects.get().unit_cost,
            Decimal("500.00"),
        )

    def test_zero_stock_quantity_is_a_no_op(self):
        DjangoStockTransactionGateway().create_stock_in(StockInRequest(
            business_id=self.business.id,
            purchase_order_id=self.purchase_order.id,
            goods_receipt_id=1,
            purchase_order_item_id=self.purchase_order_item.id,
            ingredient_id=self.ingredient.id,
            quantity=Decimal("0"),
        ))

        self.assertFalse(Stock.objects.exists())

    def test_exactly_one_active_default_warehouse_is_used(self):
        DjangoStockTransactionGateway().create_stock_in(StockInRequest(
            business_id=self.business.id,
            purchase_order_id=self.purchase_order.id,
            goods_receipt_id=1,
            purchase_order_item_id=self.purchase_order_item.id,
            ingredient_id=self.ingredient.id,
            quantity=Decimal("1"),
        ))

        self.assertTrue(
            Stock.objects.filter(
                warehouse=self.warehouse,
                ingredient=self.ingredient,
            ).exists()
        )

    def test_zero_active_default_warehouses_is_rejected(self):
        self.warehouse.is_default = False
        self.warehouse.save(update_fields=["is_default", "updated_at"])

        with self.assertRaisesRegex(ValueError, "active default warehouse"):
            DjangoStockTransactionGateway().create_stock_in(StockInRequest(
                business_id=self.business.id,
                purchase_order_id=self.purchase_order.id,
                goods_receipt_id=1,
                purchase_order_item_id=self.purchase_order_item.id,
                ingredient_id=self.ingredient.id,
                quantity=Decimal("1"),
            ))

    def test_multiple_active_default_warehouses_is_rejected(self):
        Warehouse.objects.create(
            business=self.business,
            name="Secondary",
            is_default=True,
        )

        with self.assertRaisesRegex(ValueError, "Multiple active default"):
            DjangoStockTransactionGateway().create_stock_in(StockInRequest(
                business_id=self.business.id,
                purchase_order_id=self.purchase_order.id,
                goods_receipt_id=1,
                purchase_order_item_id=self.purchase_order_item.id,
                ingredient_id=self.ingredient.id,
                quantity=Decimal("1"),
            ))

    def test_inactive_default_warehouse_is_ignored(self):
        self.warehouse.is_active = False
        self.warehouse.save(update_fields=["is_active", "updated_at"])
        active_default = Warehouse.objects.create(
            business=self.business,
            name="Active",
            is_default=True,
        )

        DjangoStockTransactionGateway().create_stock_in(StockInRequest(
            business_id=self.business.id,
            purchase_order_id=self.purchase_order.id,
            goods_receipt_id=1,
            purchase_order_item_id=self.purchase_order_item.id,
            ingredient_id=self.ingredient.id,
            quantity=Decimal("1"),
        ))

        self.assertTrue(
            Stock.objects.filter(
                warehouse=active_default,
                ingredient=self.ingredient,
            ).exists()
        )

    def test_other_business_default_warehouse_is_ignored(self):
        self.warehouse.is_default = False
        self.warehouse.save(update_fields=["is_default", "updated_at"])
        Warehouse.objects.create(
            business=self.other_business,
            name="Other",
            is_default=True,
        )

        with self.assertRaisesRegex(ValueError, "active default warehouse"):
            DjangoStockTransactionGateway().create_stock_in(StockInRequest(
                business_id=self.business.id,
                purchase_order_id=self.purchase_order.id,
                goods_receipt_id=1,
                purchase_order_item_id=self.purchase_order_item.id,
                ingredient_id=self.ingredient.id,
                quantity=Decimal("1"),
            ))

    def test_mapper_maps_the_full_aggregate(self):
        model = DjangoGoodsReceipt(
            business=self.business,
            purchase_order=self.purchase_order,
            received_by=self.user,
            received_date=datetime(2026, 9, 8, 12),
            notes="note",
        )
        model.save()
        model.items.create(
            purchase_order_item=self.purchase_order_item,
            received_quantity=Decimal("4"),
            rejected_quantity=Decimal("1"),
        )

        entity = GoodsReceiptMapper.to_domain(model)

        self.assertEqual(entity.notes, "note")
        self.assertEqual(entity.total_received_quantity, Decimal("4"))
        self.assertEqual(entity.total_rejected_quantity, Decimal("1"))
