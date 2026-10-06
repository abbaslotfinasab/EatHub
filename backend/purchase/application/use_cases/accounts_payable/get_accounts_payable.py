from purchase.domain.entities.accounts_payable import AccountsPayable
from purchase.domain.repositories.accounts_payable_repository import AccountsPayableRepository


class GetAccountsPayableUseCase:
    def __init__(self, repository: AccountsPayableRepository) -> None:
        self._repository = repository

    def execute(self, accounts_payable_id: int, business_id: int) -> AccountsPayable:
        self._positive_id(accounts_payable_id, "Accounts payable ID")
        self._positive_id(business_id, "Business ID")
        payable = self._repository.get_by_id_for_business(accounts_payable_id, business_id)
        if payable is None:
            raise ValueError("Accounts payable does not exist in this business.")
        return payable

    @staticmethod
    def _positive_id(value: int, label: str) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{label} must be a positive integer.")
