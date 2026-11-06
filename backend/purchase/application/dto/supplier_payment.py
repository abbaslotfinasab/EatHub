from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from purchase.domain.enums.payment_method import PaymentMethod


@dataclass(frozen=True)
class CreateSupplierPaymentDTO:
    business_id: int
    supplier_id: int
    amount: Decimal
    payment_date: date
    method: PaymentMethod
    idempotency_key: UUID


@dataclass(frozen=True)
class ListSupplierPaymentsQuery:
    business_id: int
    supplier_id: int | None = None
    method: PaymentMethod | None = None
    payment_date_from: date | None = None
    payment_date_to: date | None = None
