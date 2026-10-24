from datetime import date, datetime
from decimal import Decimal
from unittest import TestCase
from uuid import uuid4

from purchase.application.dto.goods_receipt import (
    CreateGoodsReceiptDTO,
    CreateGoodsReceiptItemDTO,
    ListGoodsReceiptsQuery,
)
from purchase.application.ports.goods_receipt import (
    InventoryReceiptRequest,
    PurchaseOrderLine,
)
from purchase.application.exceptions import GoodsReceiptIdempotencyPayloadMismatch
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
from purchase.domain.enums.purchase_unit import PurchaseUnit


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
        self.locked_lookup_calls = []

    def get_by_id_for_business(self, purchase_order_id, business_id):
        order = self.orders.get(purchase_order_id)
        if order is None or order.business_id != business_id:
            return None
        return order

    def get_by_id_for_business_for_update(self, purchase_order_id, business_id):
        self.locked_lookup_calls.append((purchase_order_id, business_id))
        return self.get_by_id_for_business(purchase_order_id, business_id)

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

    def get_by_idempotency_key_for_business(self, idempotency_key, business_id):
        return next(
            (
                receipt
                for receipt in self.receipts
                if receipt.business_id == business_id
                and receipt.idempotency_key == idempotency_key
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
        for index, item in enumerate(goods_receipt.items, start=1):
            item.id = item.id or (goods_receipt.id * 100 + index)
        self.saved.append(goods_receipt)
        self.receipts.append(goods_receipt)
        return goods_receipt


class FakeInventoryReceiptGateway:
    def __init__(self) -> None:
        self.requests: list[InventoryReceiptRequest] = []
        self.fail = False

    def receive_line(self, request: InventoryReceiptRequest) -> None:
        if self.fail:
            raise ValueError("Inventory receipt failed.")
        self.requests.append(request)


class GoodsReceiptApplicationTests(TestCase):
    def setUp(self) -> None:
        self.order = PurchaseOrder(
            id=10,
            business_id=1,
            supplier_id=2,
            order_date=date(2026, 9, 8),
            status=PurchaseOrderStatus.SENT,
            items=[PurchaseOrderItem(100, Decimal("10"), Decimal("2"), PurchaseUnit.KG)],
        )
        self.purchase_order_repository = FakePurchaseOrderRepository(self.order)
        self.goods_receipt_repository = FakeGoodsReceiptRepository()
        self.line_reader = FakePurchaseOrderLineReader({
            20: PurchaseOrderLine(20, 100, Decimal("10"), PurchaseUnit.KG, Decimal("2")),
        })
        self.stock_gateway = FakeInventoryReceiptGateway()
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
            "idempotency_key": uuid4(),
            "items": [
                CreateGoodsReceiptItemDTO(
                    purchase_order_item_id=20,
                    received_quantity=Decimal("4"),
                    purchase_unit=PurchaseUnit.KG,
                )
            ],
        }
        values.update(kwargs)
        return CreateGoodsReceiptDTO(**values)

    def test_creates_valid_receipt_and_partial_po(self) -> None:
        result = self.create_use_case.execute(self.command(notes="  delivery note  "))
        receipt = result.receipt

        self.assertEqual(receipt.business_id, 1)
        self.assertEqual(receipt.notes, "delivery note")
        self.assertEqual(self.order.status, PurchaseOrderStatus.PARTIAL)
        self.assertEqual(self.stock_gateway.requests[0].quantity_amount, Decimal("4"))
        self.assertEqual(self.stock_gateway.requests[0].quantity_unit, PurchaseUnit.KG)
        self.assertEqual(self.stock_gateway.requests[0].unit_cost_amount, Decimal("2"))
        self.assertEqual(self.stock_gateway.requests[0].source_document_id, receipt.id)
        self.assertEqual(self.stock_gateway.requests[0].source_line_id, receipt.items[0].id)
        self.assertEqual(self.stock_gateway.requests[0].actor_id, 3)
        self.assertTrue(self.transaction_manager.committed)
        self.assertEqual(self.purchase_order_repository.locked_lookup_calls, [(10, 1)])

    def test_same_key_and_payload_replays_without_inventory_or_po_changes(self) -> None:
        key = uuid4()
        command = self.command(idempotency_key=key)

        first = self.create_use_case.execute(command)
        saved_order_count = len(self.purchase_order_repository.saved)
        replay = self.create_use_case.execute(command)

        self.assertFalse(first.replayed)
        self.assertTrue(replay.replayed)
        self.assertEqual(replay.receipt.id, first.receipt.id)
        self.assertEqual(len(self.goods_receipt_repository.saved), 1)
        self.assertEqual(len(self.stock_gateway.requests), 1)
        self.assertEqual(len(self.purchase_order_repository.saved), saved_order_count)

    def test_replay_succeeds_after_original_receipt_completes_purchase_order(self) -> None:
        command = self.command(
            idempotency_key=uuid4(),
            items=[CreateGoodsReceiptItemDTO(20, Decimal("10"), PurchaseUnit.KG)],
        )

        first = self.create_use_case.execute(command)
        self.assertEqual(self.order.status, PurchaseOrderStatus.RECEIVED)
        order_save_count = len(self.purchase_order_repository.saved)
        lock_count = len(self.purchase_order_repository.locked_lookup_calls)

        replay = self.create_use_case.execute(command)

        self.assertTrue(replay.replayed)
        self.assertEqual(replay.receipt.id, first.receipt.id)
        self.assertEqual(self.order.status, PurchaseOrderStatus.RECEIVED)
        self.assertEqual(len(self.goods_receipt_repository.saved), 1)
        self.assertEqual(len(self.stock_gateway.requests), 1)
        self.assertEqual(len(self.purchase_order_repository.saved), order_save_count)
        self.assertEqual(len(self.purchase_order_repository.locked_lookup_calls), lock_count)

    def test_same_key_with_different_payload_conflicts_without_mutation(self) -> None:
        key = uuid4()
        first = self.create_use_case.execute(self.command(idempotency_key=key))
        order_save_count = len(self.purchase_order_repository.saved)

        with self.assertRaises(GoodsReceiptIdempotencyPayloadMismatch):
            self.create_use_case.execute(
                self.command(
                    idempotency_key=key,
                    items=[CreateGoodsReceiptItemDTO(20, Decimal("5"), PurchaseUnit.KG)],
                )
            )

        self.assertEqual(len(self.goods_receipt_repository.saved), 1)
        self.assertEqual(len(self.stock_gateway.requests), 1)
        self.assertEqual(len(self.purchase_order_repository.saved), order_save_count)
        self.assertEqual(self.goods_receipt_repository.saved[0].id, first.receipt.id)

    def test_missing_po_is_rejected_through_tenant_scoped_locked_lookup(self) -> None:
        with self.assertRaises(ValueError):
            self.create_use_case.execute(self.command(purchase_order_id=999))

        self.assertEqual(self.purchase_order_repository.locked_lookup_calls, [(999, 1)])

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
                CreateGoodsReceiptItemDTO(999, Decimal("1"), PurchaseUnit.KG),
            ]))

    def test_legacy_po_line_without_unit_cannot_be_received(self) -> None:
        self.line_reader.lines[20] = PurchaseOrderLine(
            20, 100, Decimal("10"), None, Decimal("2")
        )
        with self.assertRaisesRegex(ValueError, "legacy purchase order line has no purchase unit"):
            self.create_use_case.execute(self.command())
        self.assertEqual(self.stock_gateway.requests, [])
        self.assertTrue(self.transaction_manager.rolled_back)

    def test_goods_receipt_unit_must_match_purchase_price_basis(self) -> None:
        with self.assertRaisesRegex(ValueError, "must match the purchase order line unit"):
            self.create_use_case.execute(self.command(items=[
                CreateGoodsReceiptItemDTO(20, Decimal("1"), PurchaseUnit.G),
            ]))
        self.assertEqual(self.stock_gateway.requests, [])

    def test_receipt_inventory_cost_uses_po_unit_price_without_order_totals(self) -> None:
        self.order.discount = Decimal("5")
        self.order.tax = Decimal("4")

        self.create_use_case.execute(self.command())

        self.assertEqual(self.stock_gateway.requests[0].unit_cost_amount, Decimal("2"))
        self.assertEqual(self.stock_gateway.requests[0].unit_cost_unit, PurchaseUnit.KG)

    def test_optional_warehouse_is_forwarded_to_inventory(self) -> None:
        self.create_use_case.execute(self.command(warehouse_id=55))
        self.assertEqual(self.stock_gateway.requests[0].warehouse_id, 55)

    def test_duplicate_receipt_items_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.create_use_case.execute(self.command(items=[
                CreateGoodsReceiptItemDTO(20, Decimal("1"), PurchaseUnit.KG),
                CreateGoodsReceiptItemDTO(20, Decimal("1"), PurchaseUnit.KG),
            ]))

    def test_zero_and_negative_received_quantities_are_rejected(self) -> None:
        for quantity in (Decimal("0"), Decimal("-1")):
            with self.assertRaises(ValueError):
                self.create_use_case.execute(self.command(items=[
                    CreateGoodsReceiptItemDTO(20, quantity, PurchaseUnit.KG),
                ]))

    def test_negative_rejected_quantity_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.create_use_case.execute(self.command(items=[
                CreateGoodsReceiptItemDTO(20, Decimal("1"), PurchaseUnit.KG, Decimal("-1")),
            ]))

    def test_quantities_must_fit_persisted_decimal_precision(self) -> None:
        for accepted, rejected in (
            (Decimal("1.0001"), Decimal("0")),
            (Decimal("1.0000"), Decimal("0")),
            (Decimal("1"), Decimal("0.0001")),
            (Decimal("1000000000"), Decimal("0")),
            (Decimal("NaN"), Decimal("0")),
        ):
            with self.subTest(accepted=accepted, rejected=rejected):
                with self.assertRaises(ValueError):
                    self.create_use_case.execute(
                        self.command(
                            items=[
                                CreateGoodsReceiptItemDTO(
                                    20,
                                    accepted,
                                    PurchaseUnit.KG,
                                    rejected,
                                )
                            ]
                        )
                    )

    def test_over_receiving_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.create_use_case.execute(self.command(items=[
                CreateGoodsReceiptItemDTO(20, Decimal("11"), PurchaseUnit.KG),
            ]))

    def test_full_receipt_transitions_po_to_received(self) -> None:
        result = self.create_use_case.execute(self.command(items=[
            CreateGoodsReceiptItemDTO(20, Decimal("10"), PurchaseUnit.KG),
        ]))

        self.assertIsNotNone(result.receipt)
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
            CreateGoodsReceiptItemDTO(20, Decimal("4"), PurchaseUnit.KG),
        ]))

        self.assertEqual(self.order.status, PurchaseOrderStatus.RECEIVED)

    def test_partial_po_remains_partial_after_another_partial_receipt(self) -> None:
        self.create_use_case.execute(self.command(items=[
            CreateGoodsReceiptItemDTO(20, Decimal("4"), PurchaseUnit.KG),
        ]))

        self.assertEqual(self.order.status, PurchaseOrderStatus.PARTIAL)

    def test_rejected_quantity_does_not_create_stock_for_rejected_amount(self) -> None:
        self.create_use_case.execute(self.command(items=[
            CreateGoodsReceiptItemDTO(20, Decimal("4"), PurchaseUnit.KG, Decimal("3")),
        ]))

        self.assertEqual(len(self.stock_gateway.requests), 1)
        self.assertEqual(self.stock_gateway.requests[0].quantity_amount, Decimal("4"))

    def test_stock_rows_are_processed_in_stable_order(self) -> None:
        self.line_reader.lines[21] = PurchaseOrderLine(21, 50, Decimal("10"), PurchaseUnit.KG, Decimal("3"))
        self.create_use_case.execute(self.command(items=[
            CreateGoodsReceiptItemDTO(20, Decimal("1"), PurchaseUnit.KG),
            CreateGoodsReceiptItemDTO(21, Decimal("1"), PurchaseUnit.KG),
        ]))

        self.assertEqual(
            [request.ingredient_id for request in self.stock_gateway.requests],
            [50, 100],
        )

    def test_rejected_only_receipt_is_not_accepted_as_stock_receipt(self) -> None:
        with self.assertRaises(ValueError):
            self.create_use_case.execute(self.command(items=[
                CreateGoodsReceiptItemDTO(20, Decimal("0"), PurchaseUnit.KG, Decimal("3")),
            ]))

        self.assertEqual(self.stock_gateway.requests, [])

    def test_zero_received_quantity_with_rejected_amount_does_not_call_inventory(self) -> None:
        # A zero accepted quantity may be part of a receipt when a positive
        # rejected quantity records the physical inspection result.
        self.line_reader.lines[21] = PurchaseOrderLine(
            21, 101, Decimal("10"), PurchaseUnit.KG, Decimal("3")
        )
        self.create_use_case.execute(self.command(items=[
            CreateGoodsReceiptItemDTO(20, Decimal("0"), PurchaseUnit.KG, Decimal("3")),
            CreateGoodsReceiptItemDTO(21, Decimal("1"), PurchaseUnit.KG),
        ]))

        self.assertEqual(len(self.stock_gateway.requests), 1)
        self.assertEqual(self.stock_gateway.requests[0].source_line_id, 102)

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
