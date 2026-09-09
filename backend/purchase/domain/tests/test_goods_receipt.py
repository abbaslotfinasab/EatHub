from datetime import datetime
from decimal import Decimal
from unittest import TestCase

from purchase.domain.entities.goods_receipt import (
    GoodsReceipt,
    GoodsReceiptItem,
)


class GoodsReceiptDomainTests(TestCase):
    def create_receipt(self, **kwargs: object) -> GoodsReceipt:
        values = {
            "id": None,
            "business_id": 1,
            "purchase_order_id": 2,
            "received_by_id": 3,
            "received_date": datetime(2026, 9, 8, 10, 30),
        }
        values.update(kwargs)
        return GoodsReceipt(**values)

    def test_creates_valid_goods_receipt(self) -> None:
        receipt = self.create_receipt(
            notes="  Delivery  ",
            items=[GoodsReceiptItem(10, Decimal("4"))],
        )

        receipt.validate()

        self.assertEqual(receipt.business_id, 1)
        self.assertEqual(receipt.purchase_order_id, 2)
        self.assertEqual(receipt.received_by_id, 3)
        self.assertEqual(receipt.notes, "Delivery")

    def test_creates_valid_item(self) -> None:
        item = GoodsReceiptItem(
            purchase_order_item_id=10,
            received_quantity=Decimal("4.5"),
            rejected_quantity=Decimal("0.5"),
        )

        self.assertEqual(item.accepted_quantity, Decimal("4.5"))
        self.assertEqual(item.total_processed_quantity, Decimal("5.0"))
        self.assertTrue(item.has_rejection)

    def test_add_item_owns_item_in_aggregate(self) -> None:
        receipt = self.create_receipt()

        item = receipt.add_item(10, Decimal("2"))

        self.assertIs(receipt.items[0], item)
        self.assertTrue(receipt.has_items())
        self.assertEqual(receipt.total_items(), 1)

    def test_remove_item(self) -> None:
        receipt = self.create_receipt(
            items=[
                GoodsReceiptItem(10, Decimal("2")),
                GoodsReceiptItem(11, Decimal("3")),
            ]
        )

        receipt.remove_item(10)

        self.assertEqual(
            [item.purchase_order_item_id for item in receipt.items],
            [11],
        )

    def test_clear_items(self) -> None:
        receipt = self.create_receipt(
            items=[GoodsReceiptItem(10, Decimal("2"))]
        )

        receipt.clear_items()

        self.assertFalse(receipt.has_items())
        self.assertEqual(receipt.item_count, 0)

    def test_totals(self) -> None:
        receipt = self.create_receipt(
            items=[
                GoodsReceiptItem(10, Decimal("2"), Decimal("1")),
                GoodsReceiptItem(11, Decimal("3")),
            ]
        )

        self.assertEqual(receipt.total_received_quantity, Decimal("5"))
        self.assertEqual(receipt.total_rejected_quantity, Decimal("1"))
        self.assertEqual(receipt.total_processed_quantity, Decimal("6"))

    def test_rejects_invalid_purchase_order_item_id(self) -> None:
        with self.assertRaises(ValueError):
            GoodsReceiptItem(0, Decimal("1"))

    def test_rejects_zero_processed_quantity(self) -> None:
        with self.assertRaises(ValueError):
            GoodsReceiptItem(10, Decimal("0"), Decimal("0"))

    def test_rejects_negative_received_quantity(self) -> None:
        with self.assertRaises(ValueError):
            GoodsReceiptItem(10, Decimal("-1"))

    def test_rejects_negative_rejected_quantity(self) -> None:
        with self.assertRaises(ValueError):
            GoodsReceiptItem(10, Decimal("1"), Decimal("-1"))

    def test_rejects_missing_purchase_order_reference(self) -> None:
        with self.assertRaises(ValueError):
            self.create_receipt(purchase_order_id=0)

    def test_validate_requires_items(self) -> None:
        receipt = self.create_receipt()

        with self.assertRaises(ValueError):
            receipt.validate()

    def test_duplicate_purchase_order_items_are_rejected(self) -> None:
        receipt = self.create_receipt(
            items=[
                GoodsReceiptItem(10, Decimal("1")),
                GoodsReceiptItem(10, Decimal("2")),
            ]
        )

        with self.assertRaises(ValueError):
            receipt.validate()

        with self.assertRaises(ValueError):
            receipt.add_item(10, Decimal("3"))

    def test_remove_missing_item_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.create_receipt().remove_item(10)

    def test_rejected_only_quantity_is_valid(self) -> None:
        item = GoodsReceiptItem(
            purchase_order_item_id=10,
            received_quantity=Decimal("0"),
            rejected_quantity=Decimal("2"),
        )

        self.assertEqual(item.accepted_quantity, Decimal("0"))
        self.assertTrue(item.has_rejection)
