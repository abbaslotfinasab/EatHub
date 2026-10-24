from purchase.domain.entities.requisition import PurchaseRequisitionDecision
from purchase.domain.repositories.requisition_repository import (
    RequisitionRepository,
)


class GetRequisitionDecisionHistoryUseCase:
    def __init__(self, requisition_repository: RequisitionRepository) -> None:
        self._requisition_repository = requisition_repository

    def execute(
        self,
        requisition_id: int,
        business_id: int,
    ) -> list[PurchaseRequisitionDecision]:
        self._validate_positive_id(requisition_id, "Requisition ID")
        self._validate_positive_id(business_id, "Business ID")
        return self._requisition_repository.list_decisions_for_business(
            requisition_id=requisition_id,
            business_id=business_id,
        )

    @staticmethod
    def _validate_positive_id(value: int, field_name: str) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")
