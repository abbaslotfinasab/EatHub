from decimal import Decimal

from purchase.application.dto.requisition import (
    CreateRequisitionDTO,
    CreateRequisitionItemDTO,
)
from purchase.domain.entities.requisition import (
    PurchaseRequisition,
    PurchaseRequisitionItem,
)
from purchase.domain.enums.requisition_status import RequisitionStatus
from purchase.domain.repositories.requisition_repository import (
    RequisitionRepository,
)


class CreateRequisitionUseCase:
    def __init__(
        self,
        requisition_repository: RequisitionRepository,
    ) -> None:
        self._requisition_repository = requisition_repository

    def execute(
        self,
        command: CreateRequisitionDTO,
    ) -> PurchaseRequisition:
        business_id = self._validate_positive_id(
            command.business_id,
            "Business ID",
        )
        requested_by_id = self._validate_positive_id(
            command.requested_by_id,
            "Requested by ID",
        )
        reason = self._normalize_optional_text(command.reason, "Reason")
        items = self._normalize_items(command.items)

        requisition = PurchaseRequisition(
            id=None,
            business_id=business_id,
            requested_by_id=requested_by_id,
            status=RequisitionStatus.DRAFT,
            reason=reason,
            items=items,
        )

        return self._requisition_repository.save(requisition)

    @staticmethod
    def _validate_positive_id(value: int, field_name: str) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")

        return value

    @staticmethod
    def _validate_positive_quantity(value: Decimal) -> Decimal:
        if not isinstance(value, Decimal):
            raise ValueError("Quantity must be a decimal.")

        if value <= 0:
            raise ValueError("Quantity must be greater than zero.")

        return value

    @staticmethod
    def _normalize_optional_text(value: str, field_name: str) -> str:
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string.")

        return value.strip()

    @classmethod
    def _normalize_items(
        cls,
        items: list[CreateRequisitionItemDTO],
    ) -> list[PurchaseRequisitionItem]:
        if not items:
            raise ValueError("Purchase requisition must contain at least one item.")

        return [
            PurchaseRequisitionItem(
                ingredient_id=cls._validate_positive_id(
                    item.ingredient_id,
                    "Ingredient ID",
                ),
                quantity=cls._validate_positive_quantity(item.quantity),
                note=cls._normalize_optional_text(item.note, "Note"),
            )
            for item in items
        ]
