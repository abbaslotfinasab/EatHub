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
from purchase.application.exceptions import PurchaseInventoryIntegrationError
from purchase.application.ports.goods_receipt import InventoryReceiptRequest


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
        )
        context = InventoryExecutionContext(
            business_id=request.business_id,
            actor_id=request.actor_id,
        )
        try:
            self._receive_stock.execute(command, context)
        except (InventoryApplicationError, InventoryDomainError) as error:
            raise PurchaseInventoryIntegrationError(str(error)) from error
