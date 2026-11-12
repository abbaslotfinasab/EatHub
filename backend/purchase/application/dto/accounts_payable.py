from dataclasses import dataclass
from datetime import date

from purchase.domain.enums.accounts_payable_status import AccountsPayableStatus


@dataclass(frozen=True)
class ListAccountsPayablesQuery:
    business_id: int
    status: AccountsPayableStatus | None = None
    supplier_id: int | None = None
    due_date_from: date | None = None
    due_date_to: date | None = None
