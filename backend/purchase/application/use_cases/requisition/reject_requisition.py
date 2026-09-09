from purchase.domain.entities.requisition import PurchaseRequisition
from purchase.domain.repositories.requisition_repository import (
    RequisitionRepository,
)


class RejectRequisitionUseCase:
    def __init__(
        self,
        requisition_repository: RequisitionRepository,
    ) -> None:
        self._requisition_repository = requisition_repository

    def execute(
        self,
        requisition_id: int,
        business_id: int,
    ) -> PurchaseRequisition:
        requisition = self._get_requisition_for_business(
            requisition_id,
            business_id,
        )

        requisition.reject()

        return self._requisition_repository.save(requisition)

    def _get_requisition_for_business(
        self,
        requisition_id: int,
        business_id: int,
    ) -> PurchaseRequisition:
        validated_requisition_id = self._validate_positive_id(
            requisition_id,
            "Requisition ID",
        )
        validated_business_id = self._validate_positive_id(
            business_id,
            "Business ID",
        )

        requisition = self._requisition_repository.get_by_id_for_business(
            validated_requisition_id,
            validated_business_id,
        )

        if requisition is None:
            raise ValueError("Requisition does not exist in this business.")

        return requisition

    @staticmethod
    def _validate_positive_id(value: int, field_name: str) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")

        return value
