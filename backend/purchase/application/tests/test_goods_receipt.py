from datetime import date, datetime
from decimal import Decimal
from unittest import TestCase

from purchase.application.dto.goods_receipt import (
    CreateGoodsReceiptDTO,
    CreateGoodsReceiptItemDTO,
    ListGoodsReceiptsQuery,
)
from purchase.application.ports.goods_receipt import (
    PurchaseOrderLine,
    StockInRequest,
)
from purchase.application.use_cases.goods_receipt.create_goods_receipt import (
    CreateGoodsReceiptUseCase,
)
from purchase.application.use_cases.goods_receipt.get_goods_receipt import (
    GetGoodsReceiptUseCase,
)
from purchase.application.use_cases.goods_receipt.list_goods_receipts import (
    ListGoodsReceiptsUseCase,
)
from purchase.domain.entities.goods_receipt import GoodsReceipt, GoodsReceiptItem
from purchase.domain.entities.purchase_order import (
    PurchaseOrder,
    PurchaseOrderItem,
)
from purchase.domain.enums.purchase_order_status import PurchaseOrderStatus


class FakeTransactionManager:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    def atomic(self):
        manager = self

        class AtomicContext:
            def __enter__(self):
                return self

            def __exit__(self, exception_type, exception, traceback):
                if exception_type is None:
                    manager.committed = True
                else:
                    manager.rolled_back = True
                return False

        return AtomicContext()


class FakePurchaseOrderRepository:
    def __init__(self, order: PurchaseOrder | None = None) -> None:
        self.orders = {} if order is None else {order.id: order}
        self.saved: list[PurchaseOrder] = []
        self.fail_on_save = False

    def get_by_id_for_business(self, purchase_order_id, business_id):
        order = self.orders.get(purchase_order_id)
        if order is None or order.business_id != business_id:
            return None
        return order

    def save(self, purchase_order):
        if self.fail_on_save:
            raise ValueError("Purchase order persistence failed.")
        self.orders[purchase_order.id] = purchase_order
        self.saved.append(purchase_order)
        return purchase_order


class FakePurchaseOrderLineReader:
    def __init__(self, lines: dict[int, PurchaseOrderLine]) -> None:
        self.lines = lines
        self.calls: list[tuple[int, int]] = []

    def get_lines(self, purchase_order_id, business_id):
        self.calls.append((purchase_order_id, business_id))
        return self.lines


class FakeGoodsReceiptRepository:
    def __init__(self, receipts: list[GoodsReceipt] | None = None) -> None:
        self.receipts = receipts or []
        self.saved: list[GoodsReceipt] = []
        self.fail_on_save = False

    def get_by_id_for_business(self, goods_receipt_id, business_id):
        return next(
            (
                receipt
                for receipt in self.receipts
                if receipt.id == goods_receipt_id
                and receipt.business_id == business_id
            ),
            None,
        )

    def list(self, business_id, *, purchase_order_id=None, **kwargs):
        return [
            receipt
            for receipt in self.receipts
            if receipt.business_id == business_id
            and (
                purchase_order_id is None
                or receipt.purchase_order_id == purchase_order_id
            )
        ]

    def save(self, goods_receipt):
        if self.fail_on_save:
            raise ValueError("Goods receipt persistence failed.")
        if goods_receipt.id is None:
            goods_receipt.id = len(self.receipts) + len(self.saved) + 1
        self.saved.append(goods_receipt)
        return goods_receipt


class FakeStockTransactionGateway:
    def __init__(self) -> None:
        self.requests: list[StockInRequest] = []
        self.fail = False

    def create_stock_in(self, request: StockInRequest) -> None:
        if self.fail:
            raise ValueError("Stock transaction failed.")
        self.requests.append(request)


class GoodsReceiptApplicationTests(TestCase):
    def setUp(self) -> None:
        self.order = PurchaseOrder(
            id=10,
            business_id=1,
            supplier_id=2,
            order_date=date(2026, 9, 8),
            status=PurchaseOrderStatus.SENT,
            items=[PurchaseOrderItem(100, Decimal("10"), Decimal("2"))],
        )
        self.purchase_order_repository = FakePurchaseOrderRepository(self.order)
        self.goods_receipt_repository = FakeGoodsReceiptRepository()
        self.line_reader = FakePurchaseOrderLineReader({
            20: PurchaseOrderLine(20, 100, Decimal("10")),
        })
        self.stock_gateway = FakeStockTransactionGateway()
        self.transaction_manager = FakeTransactionManager()
        self.create_use_case = CreateGoodsReceiptUseCase(
            self.goods_receipt_repository,
            self.purchase_order_repository,
            self.line_reader,
            self.stock_gateway,
            self.transaction_manager,
        )

    def command(self, **kwargs):
        values = {
            "business_id": 1,
            "purchase_order_id": 10,
            "received_by_id": 3,
            "received_date": datetime(2026, 9, 8, 12),
            "items": [
                CreateGoodsReceiptItemDTO(
                    purchase_order_item_id=20,
                    received_quantity=Decimal("4"),
                )
            ],
        }
        values.update(kwargs)
        return CreateGoodsReceiptDTO(**values)

    def test_creates_valid_receipt_and_partial_po(self) -> None:
        receipt = self.create_use_case.execute(self.command())

        self.assertEqual(receipt.business_id, 1)
        self.assertEqual(self.order.status, PurchaseOrderStatus.PARTIAL)
        self.assertEqual(self.stock_gateway.requests[0].quantity, Decimal("4"))
        self.assertTrue(self.transaction_manager.committed)

    def test_missing_po_is_rejected_and_scoped(self) -> None:
        with self.assertRaises(ValueError):
            self.create_use_case.execute(self.command(purchase_order_id=999))

        self.assertEqual(self.line_reader.calls, [])

    def test_cross_business_po_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.create_use_case.execute(self.command(business_id=2))

    def test_cancelled_po_is_rejected(self) -> None:
        self.order.status = PurchaseOrderStatus.CANCELLED

        with self.assertRaises(ValueError):
            self.create_use_case.execute(self.command())

    def test_received_po_is_rejected(self) -> None:
        self.order.status = PurchaseOrderStatus.RECEIVED

        with self.assertRaises(ValueError):
            self.create_use_case.execute(self.command())

    def test_receipt_item_must_belong_to_po(self) -> None:
        with self.assertRaises(ValueError):
            self.create_use_case.execute(self.command(items=[
                CreateGoodsReceiptItemDTO(999, Decimal("1")),
            ]))

    def test_duplicate_receipt_items_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.create_use_case.execute(self.command(items=[
                CreateGoodsReceiptItemDTO(20, Decimal("1")),
                CreateGoodsReceiptItemDTO(20, Decimal("1")),
            ]))

    def test_zero_and_negative_received_quantities_are_rejected(self) -> None:
        for quantity in (Decimal("0"), Decimal("-1")):
            with self.assertRaises(ValueError):
                self.create_use_case.execute(self.command(items=[
                    CreateGoodsReceiptItemDTO(20, quantity),
                ]))

    def test_negative_rejected_quantity_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.create_use_case.execute(self.command(items=[
                CreateGoodsReceiptItemDTO(20, Decimal("1"), Decimal("-1")),
            ]))

    def test_over_receiving_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.create_use_case.execute(self.command(items=[
                CreateGoodsReceiptItemDTO(20, Decimal("11")),
            ]))

    def test_full_receipt_transitions_po_to_received(self) -> None:
        receipt = self.create_use_case.execute(self.command(items=[
            CreateGoodsReceiptItemDTO(20, Decimal("10")),
        ]))

        self.assertIsNotNone(receipt)
        self.assertEqual(self.order.status, PurchaseOrderStatus.RECEIVED)

    def test_previous_receipts_are_counted(self) -> None:
        previous = GoodsReceipt(
            id=1,
            business_id=1,
            purchase_order_id=10,
            received_by_id=3,
            received_date=datetime(2026, 9, 8, 10),
            items=[],
        )
        previous.items = [GoodsReceiptItem(20, Decimal("6"))]
        self.goods_receipt_repository.receipts.append(previous)

        self.create_use_case.execute(self.command(items=[
            CreateGoodsReceiptItemDTO(20, Decimal("4")),
        ]))

        self.assertEqual(self.order.status, PurchaseOrderStatus.RECEIVED)

    def test_partial_po_remains_partial_after_another_partial_receipt(self) -> None:
        self.create_use_case.execute(self.command(items=[
            CreateGoodsReceiptItemDTO(20, Decimal("4")),
        ]))

        self.assertEqual(self.order.status, PurchaseOrderStatus.PARTIAL)

    def test_rejected_quantity_does_not_create_stock_for_rejected_amount(self) -> None:
        self.create_use_case.execute(self.command(items=[
            CreateGoodsReceiptItemDTO(20, Decimal("4"), Decimal("3")),
        ]))

        self.assertEqual(len(self.stock_gateway.requests), 1)
        self.assertEqual(self.stock_gateway.requests[0].quantity, Decimal("4"))

    def test_rejected_only_receipt_is_not_accepted_as_stock_receipt(self) -> None:
        with self.assertRaises(ValueError):
            self.create_use_case.execute(self.command(items=[
                CreateGoodsReceiptItemDTO(20, Decimal("0"), Decimal("3")),
            ]))

        self.assertEqual(self.stock_gateway.requests, [])

    def test_stock_failure_rolls_back_application_boundary(self) -> None:
        self.stock_gateway.fail = True

        with self.assertRaises(ValueError):
            self.create_use_case.execute(self.command())

        self.assertTrue(self.transaction_manager.rolled_back)
        self.assertEqual(self.purchase_order_repository.saved, [])

    def test_purchase_order_failure_rolls_back_application_boundary(self) -> None:
        self.purchase_order_repository.fail_on_save = True

        with self.assertRaises(ValueError):
            self.create_use_case.execute(self.command())

        self.assertTrue(self.transaction_manager.rolled_back)

    def test_get_is_tenant_scoped(self) -> None:
        receipt = GoodsReceipt(
            id=1,
            business_id=1,
            purchase_order_id=10,
            received_by_id=3,
            received_date=datetime(2026, 9, 8, 12),
        )
        self.goods_receipt_repository.receipts.append(receipt)

        self.assertIsNotNone(
            GetGoodsReceiptUseCase(self.goods_receipt_repository).execute(1, 1)
        )
        with self.assertRaises(ValueError):
            GetGoodsReceiptUseCase(self.goods_receipt_repository).execute(1, 2)

    def test_list_forwards_scoped_filters(self) -> None:
        result = ListGoodsReceiptsUseCase(
            self.goods_receipt_repository
        ).execute(
            ListGoodsReceiptsQuery(
                business_id=1,
                purchase_order_id=10,
                received_by_id=3,
                received_from=datetime(2026, 9, 8),
                received_to=datetime(2026, 9, 9),
            )
        )

        self.assertEqual(result, [])
