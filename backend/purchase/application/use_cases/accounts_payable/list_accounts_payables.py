from purchase.application.dto.accounts_payable import ListAccountsPayablesQuery
from purchase.domain.entities.accounts_payable import AccountsPayable
from purchase.domain.repositories.accounts_payable_repository import AccountsPayableRepository


class ListAccountsPayablesUseCase:
    def __init__(self, repository: AccountsPayableRepository) -> None:
        self._repository = repository

    def execute(self, query: ListAccountsPayablesQuery) -> list[AccountsPayable]:
        if not isinstance(query.business_id, int) or query.business_id <= 0:
            raise ValueError("Business ID must be a positive integer.")
        return self._repository.list(query.business_id)
