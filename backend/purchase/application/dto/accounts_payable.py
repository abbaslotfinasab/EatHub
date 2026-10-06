from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class CreateAccountsPayableDTO:
    business_id: int
    source_invoice_id: int
    due_date: date | None = None


@dataclass(frozen=True)
class ListAccountsPayablesQuery:
    business_id: int
