from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class PaymentAllocation:
    id: int | None
    invoice_id: int
    amount: Decimal

    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if self.invoice_id <= 0:
            raise ValueError(
                "Invoice ID must be greater than zero."
            )

        if self.amount <= 0:
            raise ValueError(
                "Payment allocation amount must be greater than zero."
            )
