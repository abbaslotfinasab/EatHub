from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from types import SimpleNamespace
from unittest import TestCase

from purchase.application.purchase_invoice_audit_snapshot import (
    build_purchase_invoice_snapshot,
    json_safe,
)


class AuditSnapshotTests(TestCase):
    def test_json_safe_normalizes_nested_values(self):
        class Status(Enum):
            APPROVED = "approved"

        value = {
            "amount": Decimal("12.30"),
            "date": date(2026, 11, 23),
            "occurred_at": datetime(2026, 11, 23, 12, 30, tzinfo=timezone.utc),
            "status": Status.APPROVED,
            "nested": [Decimal("1.25"), (Status.APPROVED,)],
        }

        self.assertEqual(
            json_safe(value),
            {
                "amount": "12.30",
                "date": "2026-11-23",
                "occurred_at": "2026-11-23T12:30:00+00:00",
                "status": "approved",
                "nested": ["1.25", ["approved"]],
            },
        )

    def test_builds_compatible_invoice_snapshot(self):
        item = SimpleNamespace(
            id=8,
            ingredient_id=13,
            purchase_order_item_id=21,
            quantity=Decimal("2.500"),
            unit_price=Decimal("4.20"),
            discount_percent=Decimal("0.00"),
            tax_percent=Decimal("9.00"),
            total_price=Decimal("10.50"),
        )
        invoice = SimpleNamespace(
            invoice_number="INV-001",
            invoice_date=date(2026, 11, 23),
            supplier_id=5,
            purchase_order_id=7,
            status="approved",
            subtotal=Decimal("10.50"),
            total_price=Decimal("10.50"),
            items=[item],
        )

        self.assertEqual(
            build_purchase_invoice_snapshot(invoice),
            {
                "invoice_number": "INV-001",
                "invoice_date": "2026-11-23",
                "supplier_id": 5,
                "purchase_order_id": 7,
                "status": "approved",
                "subtotal": "10.50",
                "total_price": "10.50",
                "items": [{
                    "id": 8,
                    "ingredient_id": 13,
                    "purchase_order_item_id": 21,
                    "quantity": "2.500",
                    "unit_price": "4.20",
                    "discount_percent": "0.00",
                    "tax_percent": "9.00",
                    "total_price": "10.50",
                }],
            },
        )
