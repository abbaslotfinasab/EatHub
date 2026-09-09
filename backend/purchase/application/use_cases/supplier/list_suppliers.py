from purchase.application.dto.supplier import ListSuppliersQuery
from purchase.domain.entities.supplier import Supplier
from purchase.domain.repositories.supplier_repository import (
    SupplierRepository,
)


class ListSuppliersUseCase:
    def __init__(
        self,
        supplier_repository: SupplierRepository,
    ) -> None:
        self._supplier_repository = supplier_repository

    def execute(
        self,
        query: ListSuppliersQuery,
    ) -> list[Supplier]:
        business_id = self._validate_business_id(query.business_id)
        is_active = self._validate_is_active(query.is_active)
        search = self._normalize_search(query.search)

        return self._supplier_repository.list(
            business_id,
            is_active=is_active,
            search=search,
        )

    @staticmethod
    def _validate_business_id(business_id: int) -> int:
        if not isinstance(business_id, int) or business_id <= 0:
            raise ValueError("Business ID must be a positive integer.")

        return business_id

    @staticmethod
    def _validate_is_active(is_active: bool | None) -> bool | None:
        if is_active is not None and not isinstance(is_active, bool):
            raise ValueError("Is active must be a boolean or None.")

        return is_active

    @staticmethod
    def _normalize_search(search: str | None) -> str | None:
        if search is None:
            return None

        if not isinstance(search, str):
            raise ValueError("Search must be a string or None.")

        return search.strip() or None
