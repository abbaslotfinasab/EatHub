from purchase.application.dto.supplier import CreateSupplierDTO
from purchase.domain.entities.supplier import Supplier
from purchase.domain.repositories.supplier_repository import (
    SupplierRepository,
)


class CreateSupplierUseCase:
    def __init__(
        self,
        supplier_repository: SupplierRepository,
    ) -> None:
        self._supplier_repository = supplier_repository

    def execute(
        self,
        command: CreateSupplierDTO,
    ) -> Supplier:
        business_id = self._normalize_business_id(command.business_id)
        name = self._normalize_required_text(command.name, "Supplier name")

        if self._supplier_repository.exists_by_name(
            business_id,
            name,
        ):
            raise ValueError(
                "A supplier with this name already exists in the business."
            )

        supplier = Supplier(
            id=None,
            business_id=business_id,
            name=name,
            phone=self._normalize_optional_text(command.phone, "Phone"),
            email=self._normalize_optional_text(command.email, "Email"),
            address=self._normalize_optional_text(command.address, "Address"),
            tax_number=self._normalize_optional_text(
                command.tax_number,
                "Tax number",
            ),
            notes=self._normalize_optional_text(command.notes, "Notes"),
        )

        return self._supplier_repository.save(supplier)

    @staticmethod
    def _normalize_business_id(business_id: int) -> int:
        if not isinstance(business_id, int) or business_id <= 0:
            raise ValueError("Business ID must be a positive integer.")

        return business_id

    @staticmethod
    def _normalize_required_text(value: str, field_name: str) -> str:
        normalized = CreateSupplierUseCase._normalize_optional_text(
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
