from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from purchase.domain.enums.accounts_payable_status import AccountsPayableStatus

MONEY_QUANTUM = Decimal("0.01")


@dataclass
class AccountsPayable:
    id: int | None
    business_id: int
    supplier_id: int
    source_invoice_id: int
    amount: Decimal
    due_date: date | None = None
    status: AccountsPayableStatus = AccountsPayableStatus.OPEN
    posted_at: datetime | None = None
    posted_by_id: int | None = None
    cancelled_at: datetime | None = None
    cancelled_by_id: int | None = None
    cancellation_reason: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise ValueError("Accounts payable amount must be a Decimal.")
        self.amount = self.amount.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)
        try:
            self.status = AccountsPayableStatus(self.status)
        except (TypeError, ValueError) as error:
            raise ValueError("Invalid accounts payable status.") from error
        self.validate()

    def validate(self) -> None:
        for value, label in (
            (self.business_id, "Business ID"),
            (self.supplier_id, "Supplier ID"),
            (self.source_invoice_id, "Source invoice ID"),
        ):
            if not isinstance(value, int) or value <= 0:
                raise ValueError(f"{label} must be a positive integer.")
        if self.id is not None and (not isinstance(self.id, int) or self.id <= 0):
            raise ValueError("Accounts payable ID must be a positive integer.")
        if self.amount <= 0:
            raise ValueError("Accounts payable amount must be greater than zero.")
        if self.id is None and self.status != AccountsPayableStatus.OPEN:
            raise ValueError("New accounts payable must start as open.")
        if self.id is None and any((
            self.posted_at is not None,
            self.posted_by_id is not None,
            self.cancelled_at is not None,
            self.cancelled_by_id is not None,
            bool(self.cancellation_reason),
        )):
            raise ValueError("New accounts payable cannot have posting or cancellation metadata.")
