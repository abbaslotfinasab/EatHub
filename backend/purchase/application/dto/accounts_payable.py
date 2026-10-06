from dataclasses import dataclass
@dataclass(frozen=True)
class ListAccountsPayablesQuery:
    business_id: int
