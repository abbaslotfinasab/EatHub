from purchase.domain.entities.supplier import Supplier
from purchase.domain.repositories.supplier_repository import (
    SupplierRepository,
)


class GetSupplierUseCase:
    def __init__(
        self,
        supplier_repository: SupplierRepository,
    ) -> None:
        self._supplier_repository = supplier_repository

    def execute(
        self,
        supplier_id: int,
        business_id: int,
    ) -> Supplier:
        validated_supplier_id = self._validate_positive_id(
            supplier_id,
            "Supplier ID",
        )
        validated_business_id = self._validate_positive_id(
            business_id,
            "Business ID",
        )

        supplier = self._supplier_repository.get_by_id_for_business(
            validated_supplier_id,
            validated_business_id,
        )

        if supplier is None:
            raise ValueError("Supplier does not exist in this business.")

        return supplier

    @staticmethod
    def _validate_positive_id(value: int, field_name: str) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")

        return value
