"""Versioned canonical payload fingerprinting for supplier payment creation."""

import hashlib
import json
from decimal import Decimal

from purchase.application.dto.supplier_payment import CreateSupplierPaymentDTO


CANONICALIZATION_VERSION = 1


def supplier_payment_payload_fingerprint(command: CreateSupplierPaymentDTO) -> str:
    payload = {
        "business_id": command.business_id,
        "supplier_id": command.supplier_id,
        "amount": format(command.amount.quantize(Decimal("0.01")), "f"),
        "payment_date": command.payment_date.isoformat(),
        "method": command.method.value,
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    versioned = (
        f"purchase.supplier_payment.create:v{CANONICALIZATION_VERSION}\n"
        f"{canonical}"
    )
    return hashlib.sha256(versioned.encode("utf-8")).hexdigest()
