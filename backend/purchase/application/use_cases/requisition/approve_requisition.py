from purchase.domain.entities.requisition import PurchaseRequisition
from purchase.domain.repositories.requisition_repository import (
    RequisitionRepository,
)


class ApproveRequisitionUseCase:
    """Apply a decision; actor_id is an identifier, not proof of identity.

    HTTP adapters must provide the authenticated request user. Non-HTTP
    callers need a trusted actor and authorization boundary of their own.
    """

    def __init__(
        self,
        requisition_repository: RequisitionRepository,
    ) -> None:
        self._requisition_repository = requisition_repository

    def execute(
        self,
        requisition_id: int,
        business_id: int,
        actor_id: int,
    ) -> PurchaseRequisition:
        validated_requisition_id = self._validate_positive_id(
            requisition_id,
            "Requisition ID",
        )
        validated_business_id = self._validate_positive_id(
            business_id,
            "Business ID",
        )
        validated_actor_id = self._validate_positive_id(actor_id, "Actor ID")
        return self._requisition_repository.record_decision(
            requisition_id=validated_requisition_id,
            business_id=validated_business_id,
            actor_id=validated_actor_id,
            decision="approved",
        )

    @staticmethod
    def _validate_positive_id(value: int, field_name: str) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")

        return value
