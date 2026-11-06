"""Versioned canonical payload fingerprinting for payment allocation creation."""

import hashlib
import json
from decimal import Decimal

from purchase.application.dto.payment_allocation import CreatePaymentAllocationCommand


CANONICALIZATION_VERSION = 1


def payment_allocation_payload_fingerprint(command: CreatePaymentAllocationCommand) -> str:
    """Hash the financial intent; allocated_at is server-generated and excluded."""
    payload = {
        "business_id": command.business_id,
        "accounts_payable_id": command.accounts_payable_id,
        "supplier_payment_id": command.supplier_payment_id,
        "amount": format(command.amount.quantize(Decimal("0.01")), "f"),
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    versioned = (
        f"purchase.payment_allocation.create:v{CANONICALIZATION_VERSION}\n"
        f"{canonical}"
    )
    return hashlib.sha256(versioned.encode("utf-8")).hexdigest()
