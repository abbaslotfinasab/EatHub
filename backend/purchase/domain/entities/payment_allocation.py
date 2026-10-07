from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from purchase.domain.entities.accounts_payable import MONEY_QUANTUM


@dataclass(frozen=True)
class PaymentAllocation:
    id: int | None
    business_id: int
    accounts_payable_id: int
    supplier_payment_id: int
    amount: Decimal
    allocated_at: datetime
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise ValueError("Payment allocation amount must be a Decimal.")
        object.__setattr__(
            self,
            "amount",
            self.amount.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP),
        )
        self.validate()

    def validate(self) -> None:
        for value, label in (
            (self.business_id, "Business ID"),
            (self.accounts_payable_id, "Accounts payable ID"),
            (self.supplier_payment_id, "Supplier payment ID"),
        ):
            if not isinstance(value, int) or value <= 0:
                raise ValueError(f"{label} must be a positive integer.")
        if self.id is not None and (not isinstance(self.id, int) or self.id <= 0):
            raise ValueError("Payment allocation ID must be a positive integer.")
        if self.amount <= 0:
            raise ValueError("Payment allocation amount must be greater than zero.")
        if self.allocated_at is None:
            raise ValueError("Payment allocation timestamp is required.")
