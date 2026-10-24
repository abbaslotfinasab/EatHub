from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest import TestCase
from uuid import uuid4

from purchase.application.dto.goods_receipt import (
    CreateGoodsReceiptDTO,
    CreateGoodsReceiptItemDTO,
)
from purchase.application.use_cases.goods_receipt.canonicalization import (
    CANONICALIZATION_VERSION,
    goods_receipt_payload_fingerprint,
)
from purchase.domain.enums.purchase_unit import PurchaseUnit


class GoodsReceiptCanonicalizationTests(TestCase):
    def command(self, **overrides):
        values = {
            "business_id": 8,
            "purchase_order_id": 17,
            "received_by_id": 21,
            "received_date": datetime(2026, 10, 2, 12, tzinfo=timezone.utc),
            "items": [
                CreateGoodsReceiptItemDTO(
                    4, Decimal("1"), PurchaseUnit.KG, Decimal("0")
                ),
                CreateGoodsReceiptItemDTO(
                    9, Decimal("2.500"), PurchaseUnit.L, Decimal("0.250")
                ),
            ],
            "idempotency_key": uuid4(),
            "notes": " delivery ",
            "warehouse_id": None,
        }
        values.update(overrides)
        return CreateGoodsReceiptDTO(**values)

    def test_versioned_canonicalization_ignores_line_order_and_decimal_scale(self):
        first = self.command()
        reordered = replace(
            first,
            items=[
                CreateGoodsReceiptItemDTO(
                    9, Decimal("2.5"), PurchaseUnit.L, Decimal("0.25")
                ),
                CreateGoodsReceiptItemDTO(4, Decimal("1.000"), PurchaseUnit.KG),
            ],
            notes="delivery",
            idempotency_key=uuid4(),
            received_by_id=99,
            received_date=datetime(
                2026, 10, 2, 15, tzinfo=timezone(timedelta(hours=3))
            ),
        )

        self.assertEqual(CANONICALIZATION_VERSION, 1)
        self.assertEqual(
            goods_receipt_payload_fingerprint(first),
            goods_receipt_payload_fingerprint(reordered),
        )

    def test_business_relevant_fields_change_the_fingerprint(self):
        original = self.command()
        original_hash = goods_receipt_payload_fingerprint(original)
        variants = [
            replace(original, business_id=9),
            replace(original, purchase_order_id=18),
            replace(original, received_date=datetime(2026, 10, 3, 12, tzinfo=timezone.utc)),
            replace(original, notes="other"),
            replace(original, warehouse_id=5),
            replace(
                original,
                items=[replace(original.items[0], received_quantity=Decimal("1.001")), original.items[1]],
            ),
            replace(
                original,
                items=[replace(original.items[0], rejected_quantity=Decimal("0.001")), original.items[1]],
            ),
            replace(
                original,
                items=[replace(original.items[0], purchase_unit=PurchaseUnit.G), original.items[1]],
            ),
        ]

        for changed in variants:
            with self.subTest(changed=changed):
                self.assertNotEqual(
                    goods_receipt_payload_fingerprint(changed),
                    original_hash,
                )
