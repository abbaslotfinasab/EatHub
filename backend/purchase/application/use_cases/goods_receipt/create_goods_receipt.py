from datetime import datetime
from decimal import Decimal, InvalidOperation
from uuid import UUID

from purchase.application.dto.goods_receipt import (
    CreateGoodsReceiptDTO,
    CreateGoodsReceiptItemDTO,
    GoodsReceiptCreationResult,
)
from purchase.application.exceptions import (
    GoodsReceiptIdempotencyKeyRace,
    GoodsReceiptIdempotencyPayloadMismatch,
)
from purchase.application.use_cases.goods_receipt.canonicalization import (
    CANONICALIZATION_VERSION,
    goods_receipt_payload_fingerprint,
)
from purchase.application.ports.goods_receipt import (
    InventoryReceiptGateway,
    InventoryReceiptRequest,
    PurchaseOrderLineReader,
    TransactionManager,
)
from purchase.domain.entities.goods_receipt import (
    GoodsReceipt,
    GoodsReceiptItem,
)
from purchase.domain.enums.purchase_order_status import PurchaseOrderStatus
from purchase.domain.enums.purchase_unit import PurchaseUnit
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
        inventory_receipt_gateway: InventoryReceiptGateway,
        transaction_manager: TransactionManager,
    ) -> None:
        self._goods_receipt_repository = goods_receipt_repository
        self._purchase_order_repository = purchase_order_repository
        self._purchase_order_line_reader = purchase_order_line_reader
        self._inventory_receipt_gateway = inventory_receipt_gateway
        self._transaction_manager = transaction_manager

    def execute(self, command: CreateGoodsReceiptDTO) -> GoodsReceiptCreationResult:
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
        idempotency_key = self._validate_idempotency_key(command.idempotency_key)
        self._validate_optional_id(command.warehouse_id, "Warehouse ID")
        normalized_command = CreateGoodsReceiptDTO(
            business_id=business_id,
            purchase_order_id=purchase_order_id,
            received_by_id=received_by_id,
            received_date=received_date,
            items=item_commands,
            idempotency_key=idempotency_key,
            notes=notes,
            warehouse_id=command.warehouse_id,
        )
        fingerprint = goods_receipt_payload_fingerprint(normalized_command)

        try:
            with self._transaction_manager.atomic():
                existing = self._goods_receipt_repository.get_by_idempotency_key_for_business(
                    idempotency_key,
                    business_id,
                )
                if existing is not None:
                    return self._replay_result(existing, fingerprint)

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

                # A competing request for this PO may have committed while we
                # waited for its row lock. Resolve its key before validating
                # the PO's now-updated status.
                existing = self._goods_receipt_repository.get_by_idempotency_key_for_business(
                    idempotency_key,
                    business_id,
                )
                if existing is not None:
                    return self._replay_result(existing, fingerprint)

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
                    warehouse_id=command.warehouse_id,
                    items=receipt_items,
                    idempotency_key=idempotency_key,
                    payload_fingerprint=fingerprint,
                    payload_version=CANONICALIZATION_VERSION,
                )
                receipt.validate()

                if self._is_fully_received(lines, previous_received, current_received):
                    purchase_order.mark_received()
                elif purchase_order.status == PurchaseOrderStatus.SENT:
                    purchase_order.mark_partially_received()

                saved_receipt = self._goods_receipt_repository.save(receipt)
                self._create_inventory_receipts(
                    saved_receipt,
                    lines,
                )
                self._purchase_order_repository.save(purchase_order)
                return GoodsReceiptCreationResult(saved_receipt, replayed=False)
        except GoodsReceiptIdempotencyKeyRace as race:
            # The repository has already rolled back the failed header-insert
            # savepoint. Leaving this outer atomic block rolls back the whole
            # losing attempt before this scoped recovery query runs.
            winner = self._goods_receipt_repository.get_by_idempotency_key_for_business(
                idempotency_key,
                business_id,
            )
            if winner is None:
                raise race.original_error
            return self._replay_result(winner, fingerprint)

    @staticmethod
    def _replay_result(
        existing: GoodsReceipt,
        fingerprint: str,
    ) -> GoodsReceiptCreationResult:
        if (
            existing.payload_version != CANONICALIZATION_VERSION
            or existing.payload_fingerprint != fingerprint
        ):
            raise GoodsReceiptIdempotencyPayloadMismatch(
                "This idempotency key was already used with different receipt data."
            )
        return GoodsReceiptCreationResult(existing, replayed=True)

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
            line = lines[item.purchase_order_item_id]
            if line.purchase_unit is None:
                raise ValueError(
                    "This legacy purchase order line has no purchase unit. "
                    "Correct the line explicitly before receiving it."
                )
            if item.purchase_unit != line.purchase_unit:
                raise ValueError(
                    "Goods receipt unit must match the purchase order line unit."
                )
            receipt_items.append(
                GoodsReceiptItem(
                    purchase_order_item_id=item.purchase_order_item_id,
                    received_quantity=item.received_quantity,
                    rejected_quantity=item.rejected_quantity,
                    purchase_unit=item.purchase_unit,
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

    def _create_inventory_receipts(
        self,
        receipt: GoodsReceipt,
        lines: dict,
    ) -> None:
        # Stock rows are locked by the gateway; visit them in a stable order
        # so multi-line receipts do not acquire stock locks in payload order.
        for item in sorted(
            receipt.items,
            key=lambda row: (
                lines[row.purchase_order_item_id].ingredient_id,
                row.purchase_order_item_id,
            ),
        ):
            if item.received_quantity <= 0:
                continue
            if receipt.id is None or item.id is None or item.purchase_unit is None:
                raise ValueError(
                    "Persisted Goods Receipt and line identities and unit are required "
                    "before Inventory can receive stock."
                )
            line = lines[item.purchase_order_item_id]
            if line.purchase_unit is None:
                raise ValueError(
                    "This legacy purchase order line has no purchase unit. "
                    "Correct the line explicitly before receiving it."
                )
            self._inventory_receipt_gateway.receive_line(
                InventoryReceiptRequest(
                    business_id=receipt.business_id,
                    ingredient_id=lines[item.purchase_order_item_id].ingredient_id,
                    warehouse_id=receipt.warehouse_id,
                    quantity_amount=item.received_quantity,
                    quantity_unit=item.purchase_unit,
                    unit_cost_amount=line.unit_price,
                    unit_cost_unit=line.purchase_unit,
                    source_document_id=receipt.id,
                    source_line_id=item.id,
                    operation_kind="receive_stock",
                    actor_id=receipt.received_by_id,
                )
            )

    @classmethod
    def _validate_item_commands(cls, items: list) -> list:
        if not items:
            raise ValueError("Goods receipt must contain at least one item.")
        item_ids: set[int] = set()
        received_total = Decimal("0")
        for item in items:
            if not isinstance(item, CreateGoodsReceiptItemDTO):
                raise ValueError("Goods receipt items are invalid.")
            cls._validate_positive_id(item.purchase_order_item_id, "Purchase order item ID")
            cls._validate_decimal(item.received_quantity, "Received quantity")
            cls._validate_decimal(item.rejected_quantity, "Rejected quantity")
            if item.received_quantity < 0 or item.rejected_quantity < 0:
                raise ValueError("Receipt quantities cannot be negative.")
            if not isinstance(item.purchase_unit, PurchaseUnit):
                raise ValueError("Goods receipt purchase unit is invalid.")
            if item.purchase_order_item_id in item_ids:
                raise ValueError("A purchase order item cannot appear more than once in a receipt.")
            item_ids.add(item.purchase_order_item_id)
            if item.received_quantity == 0 and item.rejected_quantity == 0:
                raise ValueError("Received or rejected quantity must be greater than zero.")
            received_total += item.received_quantity
        if received_total <= 0:
            raise ValueError("Goods receipt must contain a positive received quantity.")
        return items

    @staticmethod
    def _validate_idempotency_key(value: UUID) -> UUID:
        if not isinstance(value, UUID):
            raise ValueError("Idempotency key must be a UUID.")
        return value

    @staticmethod
    def _validate_optional_id(value: int | None, field_name: str) -> int | None:
        if value is not None and (not isinstance(value, int) or value <= 0):
            raise ValueError(f"{field_name} must be a positive integer or None.")
        return value

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
        return value.strip()

    @staticmethod
    def _validate_decimal(value: Decimal, field_name: str) -> Decimal:
        if not isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be a decimal.")
        if not value.is_finite():
            raise ValueError(f"{field_name} must be a finite decimal.")
        try:
            normalized = value.quantize(Decimal("0.001"))
        except InvalidOperation as error:
            raise ValueError(
                f"{field_name} must fit the supported precision."
            ) from error
        decimal_places = max(0, -value.as_tuple().exponent)
        if (
            value != normalized
            or decimal_places > 3
            or abs(value) >= Decimal("1000000000")
        ):
            raise ValueError(
                f"{field_name} must fit 12 digits with at most 3 decimal places."
            )
        return value
