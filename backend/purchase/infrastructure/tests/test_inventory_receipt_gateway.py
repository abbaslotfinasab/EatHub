from decimal import Decimal
from unittest import TestCase

from inventory.application.commands import ReceiveStockCommand
from inventory.application.context import InventoryExecutionContext
from inventory.application.exceptions import OperationConflict
from inventory.domain.exceptions import IncompatibleUnits
from purchase.application.exceptions import PurchaseInventoryIntegrationError
from purchase.application.ports.goods_receipt import InventoryReceiptRequest
from purchase.domain.enums.purchase_unit import PurchaseUnit
from purchase.infrastructure.services.inventory_receipt_gateway import (
    DjangoInventoryReceiptGateway,
)


class RecordingReceiveStockUseCase:
    def __init__(self, failure=None):
        self.calls = []
        self.failure = failure

    def execute(self, command, context):
        self.calls.append((command, context))
        if self.failure is not None:
            raise self.failure


class InventoryReceiptGatewayTests(TestCase):
    def test_maps_purchase_contract_to_inventory_application_only(self):
        use_case = RecordingReceiveStockUseCase()
        gateway = DjangoInventoryReceiptGateway(use_case)

        gateway.receive_line(
            InventoryReceiptRequest(
                business_id=7,
                ingredient_id=81,
                warehouse_id=None,
                quantity_amount=Decimal("500"),
                quantity_unit=PurchaseUnit.G,
                unit_cost_amount=Decimal("150"),
                unit_cost_unit=PurchaseUnit.G,
                source_document_id=900,
                source_line_id=901,
                operation_kind="receive_stock",
                actor_id=44,
            )
        )

        self.assertEqual(len(use_case.calls), 1)
        command, context = use_case.calls[0]
        self.assertIsInstance(command, ReceiveStockCommand)
        self.assertEqual(command.warehouse_id, None)
        self.assertEqual(command.ingredient_id, 81)
        self.assertEqual(command.quantity_amount, Decimal("500"))
        self.assertEqual(command.quantity_unit, "g")
        self.assertEqual(command.unit_cost_amount, Decimal("150"))
        self.assertEqual(command.unit_cost_unit, "g")
        self.assertEqual(command.source.source_type, "goods_receipt")
        self.assertEqual(command.source.source_document_id, 900)
        self.assertEqual(command.source.source_line_id, 901)
        self.assertEqual(command.source.operation_kind, "receive_stock")
        self.assertEqual(context, InventoryExecutionContext(7, actor_id=44))

    def test_inventory_business_errors_become_purchase_integration_errors(self):
        for error in (OperationConflict("conflict"), IncompatibleUnits("units")):
            with self.subTest(error=type(error).__name__):
                gateway = DjangoInventoryReceiptGateway(
                    RecordingReceiveStockUseCase(failure=error)
                )
                with self.assertRaises(PurchaseInventoryIntegrationError) as caught:
                    gateway.receive_line(
                        InventoryReceiptRequest(
                            business_id=1,
                            ingredient_id=2,
                            warehouse_id=3,
                            quantity_amount=Decimal("1"),
                            quantity_unit=PurchaseUnit.KG,
                            unit_cost_amount=Decimal("2"),
                            unit_cost_unit=PurchaseUnit.KG,
                            source_document_id=4,
                            source_line_id=5,
                            operation_kind="receive_stock",
                            actor_id=6,
                        )
                    )
                self.assertEqual(str(caught.exception), str(error))

    def test_unexpected_infrastructure_failure_is_not_hidden(self):
        gateway = DjangoInventoryReceiptGateway(
            RecordingReceiveStockUseCase(failure=RuntimeError("database unavailable"))
        )
        with self.assertRaisesRegex(RuntimeError, "database unavailable"):
            gateway.receive_line(
                InventoryReceiptRequest(
                    business_id=1,
                    ingredient_id=2,
                    warehouse_id=None,
                    quantity_amount=Decimal("1"),
                    quantity_unit=PurchaseUnit.PC,
                    unit_cost_amount=Decimal("2"),
                    unit_cost_unit=PurchaseUnit.PC,
                    source_document_id=4,
                    source_line_id=5,
                    operation_kind="receive_stock",
                    actor_id=6,
                )
            )
