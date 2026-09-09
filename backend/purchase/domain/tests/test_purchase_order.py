from datetime import date
from decimal import Decimal
from unittest import TestCase

from purchase.domain.entities.purchase_order import (
    PurchaseOrder,
    PurchaseOrderItem,
)
from purchase.domain.enums.purchase_order_status import (
    PurchaseOrderStatus,
)


class PurchaseOrderDomainTests(TestCase):
    def create_order(self, **kwargs: object) -> PurchaseOrder:
        values = {
            "id": None,
            "business_id": 1,
            "supplier_id": 2,
            "order_date": date(2026, 9, 7),
        }
        values.update(kwargs)
        return PurchaseOrder(**values)

    def test_creates_valid_purchase_order(self) -> None:
        order = self.create_order(requisition_id=3)

        self.assertEqual(order.business_id, 1)
        self.assertEqual(order.supplier_id, 2)
        self.assertEqual(order.requisition_id, 3)
        self.assertEqual(order.status, PurchaseOrderStatus.DRAFT)

    def test_add_item_and_aggregate_ownership(self) -> None:
        order = self.create_order()

        item = order.add_item(
            ingredient_id=4,
            quantity=Decimal("2"),
            unit_price=Decimal("3.50"),
        )

        self.assertEqual(order.items, [item])
        self.assertEqual(order.total_amount(), Decimal("7.00"))

    def test_rejects_invalid_item_quantity(self) -> None:
        with self.assertRaises(ValueError):
            PurchaseOrderItem(
                ingredient_id=1,
                quantity=Decimal("0"),
                unit_price=Decimal("1"),
            )

    def test_rejects_negative_unit_price(self) -> None:
        with self.assertRaises(ValueError):
            PurchaseOrderItem(
                ingredient_id=1,
                quantity=Decimal("1"),
                unit_price=Decimal("-1"),
            )

    def test_calculates_line_total(self) -> None:
        item = PurchaseOrderItem(
            ingredient_id=1,
            quantity=Decimal("2.5"),
            unit_price=Decimal("4"),
        )

        self.assertEqual(item.line_total, Decimal("10.0"))

    def test_calculates_total_amount(self) -> None:
        order = self.create_order(
            items=[
                PurchaseOrderItem(1, Decimal("2"), Decimal("3")),
                PurchaseOrderItem(2, Decimal("1"), Decimal("4")),
            ],
            discount=Decimal("1"),
            tax=Decimal("2"),
        )

        self.assertEqual(order.total_amount(), Decimal("11"))

    def test_cannot_submit_without_items(self) -> None:
        with self.assertRaises(ValueError):
            self.create_order().send()

    def test_valid_lifecycle_transitions(self) -> None:
        order = self.create_order()
        order.add_item(1, Decimal("1"), Decimal("1"))

        order.send()
        order.mark_partially_received()
        order.mark_received()

        self.assertEqual(order.status, PurchaseOrderStatus.RECEIVED)

    def test_invalid_lifecycle_transition_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.create_order().mark_received()

    def test_cancellation_rules(self) -> None:
        order = self.create_order()
        order.cancel()

        with self.assertRaises(ValueError):
            order.send()

    def test_received_order_cannot_be_cancelled_or_modified(self) -> None:
        order = self.create_order()
        order.add_item(1, Decimal("1"), Decimal("1"))
        order.send()
        order.mark_received()

        with self.assertRaises(ValueError):
            order.cancel()

        with self.assertRaises(ValueError):
            order.add_item(2, Decimal("1"), Decimal("1"))

    def test_remove_and_clear_items_are_aggregate_operations(self) -> None:
        order = self.create_order()
        order.add_item(1, Decimal("1"), Decimal("1"))
        order.add_item(2, Decimal("1"), Decimal("1"))

        order.remove_item(1)
        self.assertEqual([item.ingredient_id for item in order.items], [2])

        order.clear_items()
        self.assertFalse(order.has_items())
