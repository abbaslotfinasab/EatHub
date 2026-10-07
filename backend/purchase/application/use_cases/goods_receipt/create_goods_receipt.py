from datetime import datetime
from decimal import Decimal

from purchase.application.dto.goods_receipt import CreateGoodsReceiptDTO
from purchase.application.ports.goods_receipt import (
    PurchaseOrderLineReader,
    StockInRequest,
    StockTransactionGateway,
    TransactionManager,
)
from purchase.domain.entities.goods_receipt import (
    GoodsReceipt,
    GoodsReceiptItem,
)
from purchase.domain.enums.purchase_order_status import PurchaseOrderStatus
from purchase.domain.repositories.goods_receipt_repository import (
    GoodsReceiptRepository,
)
from purchase.domain.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)


class CreateGoodsReceiptUseCase:
    def __init__(
        self,
        goods_receipt_repository: GoodsReceiptRepository,
        purchase_order_repository: PurchaseOrderRepository,
        purchase_order_line_reader: PurchaseOrderLineReader,
        stock_transaction_gateway: StockTransactionGateway,
        transaction_manager: TransactionManager,
    ) -> None:
        self._goods_receipt_repository = goods_receipt_repository
        self._purchase_order_repository = purchase_order_repository
        self._purchase_order_line_reader = purchase_order_line_reader
        self._stock_transaction_gateway = stock_transaction_gateway
        self._transaction_manager = transaction_manager

    def execute(self, command: CreateGoodsReceiptDTO) -> GoodsReceipt:
        business_id = self._validate_positive_id(command.business_id, "Business ID")
        purchase_order_id = self._validate_positive_id(
            command.purchase_order_id,
            "Purchase order ID",
        )
        received_by_id = self._validate_positive_id(
            command.received_by_id,
            "Received by ID",
        )
        received_date = self._validate_datetime(
            command.received_date,
            "Received date",
        )
        notes = self._validate_notes(command.notes)
        item_commands = self._validate_item_commands(command.items)

        with self._transaction_manager.atomic():
            purchase_order = (
                self._purchase_order_repository.get_by_id_for_business_for_update(
                    purchase_order_id,
                    business_id,
                )
            )
            if purchase_order is None:
                raise ValueError("Purchase order does not exist in this business.")
            if purchase_order.business_id != business_id:
                raise ValueError("Purchase order does not belong to this business.")

            if purchase_order.status not in (
                PurchaseOrderStatus.SENT,
                PurchaseOrderStatus.PARTIAL,
            ):
                raise ValueError(
                    "Goods receipt is only allowed for sent or partially received purchase orders."
                )

            lines = self._purchase_order_line_reader.get_lines(
                purchase_order_id,
                business_id,
            )
            if not lines:
                raise ValueError("Purchase order has no receivable items.")
            receipt_items = self._build_receipt_items(item_commands, lines)
            previous_received = self._previously_received_quantities(
                business_id,
                purchase_order_id,
            )
            current_received = self._validate_quantities(
                receipt_items,
                lines,
                previous_received,
            )

            if not any(item.received_quantity > 0 for item in receipt_items):
                raise ValueError(
                    "Goods receipt must contain a positive received quantity."
                )

            receipt = GoodsReceipt(
                id=None,
                business_id=business_id,
                purchase_order_id=purchase_order_id,
                received_by_id=received_by_id,
                received_date=received_date,
                notes=notes,
                items=receipt_items,
            )
            receipt.validate()

            if self._is_fully_received(lines, previous_received, current_received):
                purchase_order.mark_received()
            elif purchase_order.status == PurchaseOrderStatus.SENT:
                purchase_order.mark_partially_received()

            saved_receipt = self._goods_receipt_repository.save(receipt)
            self._create_stock_in_requests(
                saved_receipt,
                business_id,
                purchase_order_id,
                receipt_items,
                lines,
            )
            self._purchase_order_repository.save(purchase_order)

        return saved_receipt

    def _previously_received_quantities(
        self,
        business_id: int,
        purchase_order_id: int,
    ) -> dict[int, Decimal]:
        quantities: dict[int, Decimal] = {}
        receipts = self._goods_receipt_repository.list(
            business_id,
            purchase_order_id=purchase_order_id,
        )
        for receipt in receipts:
            if (
                receipt.business_id != business_id
                or receipt.purchase_order_id != purchase_order_id
            ):
                raise ValueError(
                    "Goods receipt repository returned an out-of-scope receipt."
                )
            for item in receipt.items:
                quantities[item.purchase_order_item_id] = quantities.get(
                    item.purchase_order_item_id,
                    Decimal("0"),
                ) + item.received_quantity
        return quantities

    @classmethod
    def _build_receipt_items(
        cls,
        item_commands: list,
        lines: dict,
    ) -> list[GoodsReceiptItem]:
        for item in item_commands:
            cls._validate_positive_id(
                item.purchase_order_item_id,
                "Purchase order item ID",
            )
            cls._validate_decimal(
                item.received_quantity,
                "Received quantity",
            )
            cls._validate_decimal(
                item.rejected_quantity,
                "Rejected quantity",
            )

        item_ids = [item.purchase_order_item_id for item in item_commands]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError(
                "A purchase order item cannot appear more than once in a receipt."
            )

        receipt_items: list[GoodsReceiptItem] = []
        for item in item_commands:
            if item.purchase_order_item_id not in lines:
                raise ValueError(
                    "Receipt item does not belong to the purchase order."
                )
            receipt_items.append(
                GoodsReceiptItem(
                    purchase_order_item_id=item.purchase_order_item_id,
                    received_quantity=item.received_quantity,
                    rejected_quantity=item.rejected_quantity,
                )
            )
        return receipt_items

    @staticmethod
    def _validate_quantities(
        receipt_items: list[GoodsReceiptItem],
        lines: dict,
        previously_received: dict[int, Decimal],
    ) -> dict[int, Decimal]:
        current_received: dict[int, Decimal] = {}
        unknown_previous_items = set(previously_received).difference(lines)
        if unknown_previous_items:
            raise ValueError(
                "Previously received item does not belong to the purchase order."
            )
        for line_id, line in lines.items():
            previous = previously_received.get(line_id, Decimal("0"))
            if previous > line.ordered_quantity:
                raise ValueError(
                    "Previously received quantity exceeds the purchase order quantity."
                )
        for item in receipt_items:
            line = lines[item.purchase_order_item_id]
            previous = previously_received.get(item.purchase_order_item_id, Decimal("0"))
            if previous + item.received_quantity > line.ordered_quantity:
                raise ValueError(
                    "Goods receipt quantity cannot exceed the purchase order quantity."
                )
            current_received[item.purchase_order_item_id] = item.received_quantity
        return current_received

    @staticmethod
    def _is_fully_received(
        lines: dict,
        previously_received: dict[int, Decimal],
        current_received: dict[int, Decimal],
    ) -> bool:
        return all(
            previously_received.get(line_id, Decimal("0"))
            + current_received.get(line_id, Decimal("0"))
            >= line.ordered_quantity
            for line_id, line in lines.items()
        )

    def _create_stock_in_requests(
        self,
        receipt: GoodsReceipt,
        business_id: int,
        purchase_order_id: int,
        items: list[GoodsReceiptItem],
        lines: dict,
    ) -> None:
        # Stock rows are locked by the gateway; visit them in a stable order
        # so multi-line receipts do not acquire stock locks in payload order.
        for item in sorted(
            items,
            key=lambda row: (
                lines[row.purchase_order_item_id].ingredient_id,
                row.purchase_order_item_id,
            ),
        ):
            if item.received_quantity <= 0:
                continue
            self._stock_transaction_gateway.create_stock_in(
                StockInRequest(
                    business_id=business_id,
                    purchase_order_id=purchase_order_id,
                    goods_receipt_id=receipt.id,
                    purchase_order_item_id=item.purchase_order_item_id,
                    ingredient_id=lines[item.purchase_order_item_id].ingredient_id,
                    quantity=item.received_quantity,
                )
            )

    @classmethod
    def _validate_item_commands(cls, items: list) -> list:
        if not items:
            raise ValueError("Goods receipt must contain at least one item.")
        return items

    @staticmethod
    def _validate_positive_id(value: int, field_name: str) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")
        return value

    @staticmethod
    def _validate_datetime(value: datetime, field_name: str) -> datetime:
        if not isinstance(value, datetime):
            raise ValueError(f"{field_name} must be a datetime.")
        return value

    @staticmethod
    def _validate_notes(value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Notes must be a string.")
        return value

    @staticmethod
    def _validate_decimal(value: Decimal, field_name: str) -> Decimal:
        if not isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be a decimal.")
        return value
