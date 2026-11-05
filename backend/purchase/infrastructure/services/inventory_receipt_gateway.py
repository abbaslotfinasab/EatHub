from inventory.application.commands import (
    OperationIdentityInput,
    ReceiveStockCommand,
)
from inventory.application.context import InventoryExecutionContext
from inventory.application.exceptions import (
    InventoryApplicationError,
    InventoryDomainError,
)
from inventory.application.use_cases.receive_stock import ReceiveStockUseCase
from inventory.infrastructure.django.models import InventoryV1StockMovement
from purchase.application.exceptions import PurchaseInventoryIntegrationError
from purchase.application.ports.goods_receipt import InventoryReceiptRequest
from purchase.models import GoodsReceiptInventoryMovementLink, GoodsReceiptItem


class DjangoInventoryReceiptGateway:
    """Translate Purchase receipt input into the public Inventory use case."""

    def __init__(self, receive_stock: ReceiveStockUseCase) -> None:
        self._receive_stock = receive_stock

    def receive_line(self, request: InventoryReceiptRequest) -> None:
        command = ReceiveStockCommand(
            warehouse_id=request.warehouse_id,
            ingredient_id=request.ingredient_id,
            quantity_amount=request.quantity_amount,
            quantity_unit=request.quantity_unit.value,
            unit_cost_amount=request.unit_cost_amount,
            unit_cost_unit=request.unit_cost_unit.value,
            source=OperationIdentityInput(
                source_type="goods_receipt",
                source_document_id=request.source_document_id,
                source_line_id=request.source_line_id,
                operation_kind=request.operation_kind,
            ),
            occurred_at=request.occurred_at,
        )
        context = InventoryExecutionContext(
            business_id=request.business_id,
            actor_id=request.actor_id,
        )
        try:
            self._receive_stock.execute(command, context)
        except (InventoryApplicationError, InventoryDomainError) as error:
            raise PurchaseInventoryIntegrationError(str(error)) from error

        # Resolve the persisted ledger row by its tenant-scoped source identity,
        # then persist a protected FK from the receipt line back to that row.
        movement = InventoryV1StockMovement.objects.select_related(
            "stock"
        ).get(
            business_id=request.business_id,
            source_type="goods_receipt",
            source_document_id=request.source_document_id,
            source_line_id=request.source_line_id,
            operation_kind=request.operation_kind,
        )
        if movement.movement_type != "receipt" or movement.direction != "in":
            raise PurchaseInventoryIntegrationError(
                "Goods receipt source identity resolved to a non-receipt movement."
            )

        receipt_item = GoodsReceiptItem.objects.select_related(
            "receipt", "purchase_order_item"
        ).filter(
            pk=request.source_line_id,
            receipt_id=request.source_document_id,
            receipt__business_id=request.business_id,
            purchase_order_item__ingredient_id=request.ingredient_id,
        ).first()
        if receipt_item is None:
            raise PurchaseInventoryIntegrationError(
                "Goods receipt line does not match the persisted Inventory movement."
            )
        if movement.stock.ingredient_id != request.ingredient_id:
            raise PurchaseInventoryIntegrationError(
                "Inventory movement ingredient does not match the goods receipt line."
            )
        link, created = GoodsReceiptInventoryMovementLink.objects.get_or_create(
            receipt_item=receipt_item,
            defaults={"movement": movement},
        )
        if not created and link.movement_id != movement.pk:
            raise PurchaseInventoryIntegrationError(
                "Goods receipt line is already linked to a different Inventory movement."
            )
