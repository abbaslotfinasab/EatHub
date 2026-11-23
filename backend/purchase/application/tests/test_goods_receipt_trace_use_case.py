from datetime import datetime
from decimal import Decimal

from django.test import SimpleTestCase

from purchase.application.exceptions import GoodsReceiptTraceUnavailable
from purchase.application.ports.goods_receipt_trace import (
    GoodsReceiptMovementLinkRecord,
    StockMovementTraceRecord,
)
from purchase.application.use_cases.goods_receipt.trace_stock_movement import (
    TraceGoodsReceiptStockMovementUseCase,
)


class FakeTraceReader:
    def __init__(self, movement=None, link=None):
        self.movement = movement
        self.link = link
        self.link_calls = 0

    def get_stock_movement_for_business(self, movement_id, business_id):
        return self.movement

    def get_receipt_link_for_movement(self, movement_id, business_id):
        self.link_calls += 1
        return self.link


class GoodsReceiptStockMovementTraceUseCaseTests(SimpleTestCase):
    def setUp(self):
        self.movement = StockMovementTraceRecord(
            id=10,
            business_id=1,
            source_type="goods_receipt",
            source_document_id=20,
            source_line_id=30,
            operation_kind="receive_stock",
            movement_type="receipt",
            direction="in",
            quantity=Decimal("2.000000000000"),
            unit="kg",
            unit_cost=Decimal("15.000"),
            occurred_at=datetime(2026, 10, 2, 12),
            actor_id=4,
            stock_id=5,
            stock_business_id=1,
            warehouse_id=6,
            warehouse_name="Main",
            warehouse_business_id=1,
            ingredient_id=7,
            ingredient_name="Flour",
            ingredient_business_id=1,
        )
        self.link = GoodsReceiptMovementLinkRecord(
            receipt_id=20,
            receipt_business_id=1,
            received_date=datetime(2026, 10, 2, 12),
            received_by_id=4,
            receipt_purchase_order_id=40,
            receipt_item_id=30,
            purchase_order_item_id=50,
            received_quantity=Decimal("2.000"),
            rejected_quantity=Decimal("0.000"),
            purchase_unit="kg",
            purchase_order_id=40,
            purchase_order_business_id=1,
            purchase_order_status="partial",
            supplier_id=60,
            supplier_name="Supplier",
            supplier_business_id=1,
            purchase_order_item_purchase_order_id=40,
            purchase_order_item_ingredient_id=7,
            purchase_order_item_quantity=Decimal("10.000"),
            purchase_order_item_purchase_unit="kg",
            purchase_order_item_unit_price=Decimal("15.00"),
        )

    def test_returns_existing_trace_response_shape(self):
        use_case = TraceGoodsReceiptStockMovementUseCase(
            FakeTraceReader(self.movement, self.link)
        )

        result = use_case.execute(movement_id=10, business_id=1)

        self.assertEqual(result["movement"]["id"], 10)
        self.assertEqual(result["movement"]["warehouse_name"], "Main")
        self.assertEqual(result["goods_receipt"]["id"], 20)
        self.assertEqual(result["goods_receipt_item"]["id"], 30)
        self.assertEqual(result["purchase_order"]["supplier_name"], "Supplier")
        self.assertEqual(result["purchase_order_item"]["ingredient_id"], 7)
        self.assertEqual(result["supplier"], {"id": 60, "name": "Supplier"})

    def test_missing_movement_is_not_found_and_does_not_query_link(self):
        reader = FakeTraceReader()
        with self.assertRaisesRegex(ValueError, "does not exist"):
            TraceGoodsReceiptStockMovementUseCase(reader).execute(10, 1)
        self.assertEqual(reader.link_calls, 0)

    def test_non_receipt_movement_is_rejected_before_link_lookup(self):
        movement = StockMovementTraceRecord(
            **{**self.movement.__dict__, "source_type": "manual_adjustment"}
        )
        reader = FakeTraceReader(movement, self.link)
        with self.assertRaisesRegex(ValueError, "not a goods receipt"):
            TraceGoodsReceiptStockMovementUseCase(reader).execute(10, 1)
        self.assertEqual(reader.link_calls, 0)

    def test_missing_link_is_reported_as_unavailable_trace(self):
        with self.assertRaises(GoodsReceiptTraceUnavailable):
            TraceGoodsReceiptStockMovementUseCase(
                FakeTraceReader(self.movement)
            ).execute(10, 1)

    def test_cross_tenant_stock_reference_is_rejected(self):
        movement = StockMovementTraceRecord(
            **{**self.movement.__dict__, "warehouse_business_id": 2}
        )
        with self.assertRaisesRegex(
            GoodsReceiptTraceUnavailable, "references are inconsistent"
        ):
            TraceGoodsReceiptStockMovementUseCase(
                FakeTraceReader(movement, self.link)
            ).execute(10, 1)

    def test_receipt_and_purchase_order_mismatch_is_rejected(self):
        link = GoodsReceiptMovementLinkRecord(
            **{**self.link.__dict__, "receipt_purchase_order_id": 999}
        )
        with self.assertRaises(GoodsReceiptTraceUnavailable):
            TraceGoodsReceiptStockMovementUseCase(
                FakeTraceReader(self.movement, link)
            ).execute(10, 1)
