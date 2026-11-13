from purchase.application.dto.accounts_payable import ListAccountsPayablesQuery
from purchase.domain.entities.accounts_payable import AccountsPayable
from purchase.domain.repositories.accounts_payable_repository import AccountsPayableRepository


class ListAccountsPayablesUseCase:
    def __init__(self, repository: AccountsPayableRepository) -> None:
        self._repository = repository

    def execute(self, query: ListAccountsPayablesQuery) -> list[AccountsPayable]:
        if not isinstance(query.business_id, int) or query.business_id <= 0:
            raise ValueError("Business ID must be a positive integer.")
        if query.supplier_id is not None and (
            not isinstance(query.supplier_id, int) or query.supplier_id <= 0
        ):
            raise ValueError("Supplier ID must be a positive integer.")
        if query.due_date_from and query.due_date_to and query.due_date_from > query.due_date_to:
            raise ValueError("Due date range is invalid.")
        return self._repository.list(
            query.business_id,
            status=query.status,
            supplier_id=query.supplier_id,
            due_date_from=query.due_date_from,
            due_date_to=query.due_date_to,
        )
