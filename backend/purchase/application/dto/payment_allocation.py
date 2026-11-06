from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from purchase.domain.entities.payment_allocation import PaymentAllocation


@dataclass(frozen=True)
class CreatePaymentAllocationCommand:
    business_id: int
    accounts_payable_id: int
    supplier_payment_id: int
    amount: Decimal
    allocated_at: datetime
    idempotency_key: UUID


@dataclass(frozen=True)
class ListPaymentAllocationsQuery:
    business_id: int
    accounts_payable_id: int | None = None
    supplier_payment_id: int | None = None


@dataclass(frozen=True)
class PaymentAllocationResult:
    allocation: PaymentAllocation
    replayed: bool = False
