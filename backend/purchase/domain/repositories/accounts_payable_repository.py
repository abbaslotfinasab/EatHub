from abc import ABC, abstractmethod

from purchase.domain.entities.accounts_payable import AccountsPayable


class AccountsPayableRepository(ABC):
    @abstractmethod
    def lock_source_invoice_for_creation(self, business_id: int, source_invoice_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def create(self, accounts_payable: AccountsPayable) -> AccountsPayable:
        raise NotImplementedError

    @abstractmethod
    def get_by_id_for_business(
        self, accounts_payable_id: int, business_id: int
    ) -> AccountsPayable | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_source_invoice_id(
        self, source_invoice_id: int, business_id: int
    ) -> AccountsPayable | None:
        raise NotImplementedError

    @abstractmethod
    def list(self, business_id: int) -> list[AccountsPayable]:
        raise NotImplementedError

    @abstractmethod
    def exists_for_source_invoice(self, source_invoice_id: int, business_id: int) -> bool:
        raise NotImplementedError
