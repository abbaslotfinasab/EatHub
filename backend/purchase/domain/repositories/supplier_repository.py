from abc import ABC, abstractmethod

from purchase.domain.entities.supplier import Supplier


class SupplierRepository(ABC):

    @abstractmethod
    def get_by_id_for_business(
        self,
        supplier_id: int,
        business_id: int,
    ) -> Supplier | None:
        """
        Return a supplier by ID within a business.

        Returns:
            Supplier | None
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_name(
        self,
        business_id: int,
        name: str,
    ) -> Supplier | None:
        """
        Return a supplier by name within a business.

        Returns:
            Supplier | None
        """
        raise NotImplementedError

    @abstractmethod
    def list(
        self,
        business_id: int,
        *,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> list[Supplier]:
        """
        Return suppliers belonging to a business.
        """
        raise NotImplementedError

    @abstractmethod
    def exists_by_name(
        self,
        business_id: int,
        name: str,
        *,
        exclude_id: int | None = None,
    ) -> bool:
        """
        Check whether a supplier with the given name
        already exists within a business.
        """
        raise NotImplementedError

    @abstractmethod
    def save(
        self,
        supplier: Supplier,
    ) -> Supplier:
        """
        Create or update a supplier.
        """
        raise NotImplementedError

