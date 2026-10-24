"""Versioned canonical payload fingerprinting for goods receipt creation."""

import hashlib
import json
from datetime import timezone
from decimal import Decimal

from purchase.application.dto.goods_receipt import CreateGoodsReceiptDTO


CANONICALIZATION_VERSION = 1


def goods_receipt_payload_fingerprint(command: CreateGoodsReceiptDTO) -> str:
    """Hash validated receipt semantics, excluding generated and actor data.

    Notes are trimmed, datetimes are represented as UTC instants (naive
    application-level values are treated as UTC), and quantities are rendered
    at the API's three decimal places. Omitted/defaulted rejected quantities,
    blank notes, and omitted/null warehouse IDs therefore have one form. Lines
    are sorted by PO item ID; duplicate item IDs are rejected by the use case.
    """
    received_date = command.received_date
    if received_date.utcoffset() is None:
        received_date = received_date.replace(tzinfo=timezone.utc)
    else:
        received_date = received_date.astimezone(timezone.utc)

    payload = {
        "business_id": command.business_id,
        "purchase_order_id": command.purchase_order_id,
        "received_date": received_date.isoformat(timespec="microseconds"),
        "notes": command.notes.strip(),
        "warehouse_id": command.warehouse_id,
        "items": [
            {
                "purchase_order_item_id": item.purchase_order_item_id,
                "received_quantity": _quantity(item.received_quantity),
                "rejected_quantity": _quantity(item.rejected_quantity),
                "purchase_unit": item.purchase_unit.value,
            }
            for item in sorted(
                command.items,
                key=lambda value: value.purchase_order_item_id,
            )
        ],
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    versioned = f"purchase.goods_receipt.create:v{CANONICALIZATION_VERSION}\n{canonical}"
    return hashlib.sha256(versioned.encode("utf-8")).hexdigest()


def _quantity(value: Decimal) -> str:
    if value == 0:
        return "0.000"
    return format(value.quantize(Decimal("0.001")), "f")
