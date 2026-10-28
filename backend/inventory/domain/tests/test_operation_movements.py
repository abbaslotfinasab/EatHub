import unittest
from decimal import Decimal

from inventory.domain.entities.ingredient import Ingredient
from inventory.domain.entities.stock import Stock
from inventory.domain.entities.warehouse import Warehouse
from inventory.domain.enums.ingredient import IngredientPreparationLevel
from inventory.domain.enums.movement import MovementDirection, MovementType
from inventory.domain.exceptions import NegativeStock
from inventory.domain.value_objects.quantity import Quantity
from inventory.domain.value_objects.source_identity import SourceIdentity
from inventory.domain.value_objects.unit import Unit
from inventory.domain.value_objects.unit_cost import UnitCost


class InventoryOperationMovementTests(unittest.TestCase):
    def setUp(self):
        self.ingredient = Ingredient(10, 1, "Rice", Unit.KG, IngredientPreparationLevel.RAW)
        self.source = Warehouse(20, 1, "Main")
        self.destination = Warehouse(21, 1, "Cold")

    def seed(self, warehouse):
        stock = Stock(warehouse, self.ingredient)
        stock.receive(
            Quantity(Decimal("10"), Unit.KG), UnitCost(Decimal("4")),
            SourceIdentity(1, "test", warehouse.id, 1, "seed"), warehouse,
        )
        return stock

    def test_issue_is_outbound_auditable_and_rejects_negative_stock(self):
        stock = self.seed(self.source)
        movement = stock.issue(
            Quantity(Decimal("3"), Unit.KG),
            SourceIdentity(1, "inventory_issue", 1, 1, "post"), self.source,
            reason="Kitchen use", actor_id=7,
        )
        self.assertEqual(movement.movement_type, MovementType.ISSUE)
        self.assertEqual(movement.direction, MovementDirection.OUT)
        self.assertEqual(movement.balance_after.amount, Decimal("7"))
        self.assertEqual(movement.unit_cost.amount, Decimal("4"))
        with self.assertRaises(NegativeStock):
            stock.issue(
                Quantity(Decimal("8"), Unit.KG),
                SourceIdentity(1, "inventory_issue", 2, 1, "post"), self.source,
                reason="Too much", actor_id=7,
            )
        self.assertEqual(stock.quantity.amount, Decimal("7"))

    def test_transfer_dispatch_and_receipt_preserve_costing_and_identity(self):
        source_stock = self.seed(self.source)
        target_stock = Stock(self.destination, self.ingredient)
        outbound = source_stock.transfer_out(
            Quantity(Decimal("2"), Unit.KG),
            SourceIdentity(1, "inventory_transfer", 9, 1, "dispatch"), self.source,
            actor_id=7,
        )
        inbound = target_stock.transfer_in(
            Quantity(Decimal("2"), Unit.KG), outbound.unit_cost,
            SourceIdentity(1, "inventory_transfer", 9, 1, "receive"), self.destination,
            actor_id=8,
        )
        self.assertEqual(outbound.movement_type, MovementType.TRANSFER_DISPATCH)
        self.assertEqual(inbound.movement_type, MovementType.TRANSFER_RECEIPT)
        self.assertEqual(outbound.balance_after.amount, Decimal("8"))
        self.assertEqual(inbound.balance_after.amount, Decimal("2"))
        self.assertEqual(target_stock.average_cost.amount, Decimal("4"))
        self.assertEqual(outbound.source_identity.source_document_id, inbound.source_identity.source_document_id)

