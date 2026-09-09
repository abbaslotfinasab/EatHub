from purchase.application.dto.supplier import UpdateSupplierDTO
from purchase.domain.entities.supplier import Supplier
from purchase.domain.repositories.supplier_repository import (
    SupplierRepository,
)


class UpdateSupplierUseCase:
    def __init__(
        self,
        supplier_repository: SupplierRepository,
    ) -> None:
        self._supplier_repository = supplier_repository

    def execute(
        self,
        command: UpdateSupplierDTO,
    ) -> Supplier:
        business_id = self._validate_positive_id(
            command.business_id,
            "Business ID",
        )
        supplier_id = self._validate_positive_id(
            command.supplier_id,
            "Supplier ID",
        )
        name = self._normalize_required_text(command.name, "Supplier name")

        supplier = self._supplier_repository.get_by_id_for_business(
            supplier_id,
            business_id,
        )

        if supplier is None:
            raise ValueError("Supplier does not exist in this business.")

        if self._supplier_repository.exists_by_name(
            business_id,
            name,
            exclude_id=supplier_id,
        ):
            raise ValueError(
                "A supplier with this name already exists in the business."
            )

        supplier.name = name
        supplier.phone = self._normalize_optional_text(command.phone, "Phone")
        supplier.email = self._normalize_optional_text(command.email, "Email")
        supplier.address = self._normalize_optional_text(
            command.address,
            "Address",
        )
        supplier.tax_number = self._normalize_optional_text(
            command.tax_number,
            "Tax number",
        )
        supplier.notes = self._normalize_optional_text(command.notes, "Notes")
        supplier.is_active = self._validate_is_active(command.is_active)

        return self._supplier_repository.save(supplier)

    @staticmethod
    def _validate_positive_id(value: int, field_name: str) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")

        return value

    @staticmethod
    def _normalize_required_text(value: str, field_name: str) -> str:
        normalized = UpdateSupplierUseCase._normalize_optional_text(
            value,
            field_name,
        )

        if not normalized:
            raise ValueError(f"{field_name} cannot be empty.")

        return normalized

    @staticmethod
    def _normalize_optional_text(value: str, field_name: str) -> str:
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string.")

        return value.strip()

    @staticmethod
    def _validate_is_active(is_active: bool) -> bool:
        if not isinstance(is_active, bool):
            raise ValueError("Is active must be a boolean.")

        return is_active
