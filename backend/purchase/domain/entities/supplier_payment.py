from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from purchase.domain.enums.payment_method import PaymentMethod

MONEY_QUANTUM = Decimal("0.01")


@dataclass
class SupplierPayment:
    id: int | None

    business_id: int
    supplier_id: int

    amount: Decimal
    payment_date: date
    method: PaymentMethod

    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise ValueError("Supplier payment amount must be a Decimal.")
        self.amount = self.amount.quantize(
            MONEY_QUANTUM,
            rounding=ROUND_HALF_UP,
        )
        try:
            self.method = PaymentMethod(self.method)
        except (TypeError, ValueError) as error:
            raise ValueError("Invalid supplier payment method.") from error
        self._validate_amount()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> None:
        self._validate_ids()
        self._validate_amount()
        self._validate_payment_date()

    def _validate_ids(self) -> None:
        if not isinstance(self.business_id, int) or self.business_id <= 0:
            raise ValueError("Business ID must be a positive integer.")
        if not isinstance(self.supplier_id, int) or self.supplier_id <= 0:
            raise ValueError("Supplier ID must be a positive integer.")

    def _validate_amount(self) -> None:
        if self.amount <= 0:
            raise ValueError(
                "Supplier payment amount must be greater than zero."
            )

    def _validate_payment_date(self) -> None:
        if not self.payment_date:
            raise ValueError(
                "Payment date is required."
            )
