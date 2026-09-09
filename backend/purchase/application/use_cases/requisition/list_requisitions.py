from purchase.application.dto.requisition import ListRequisitionsQuery
from purchase.domain.entities.requisition import PurchaseRequisition
from purchase.domain.enums.requisition_status import RequisitionStatus
from purchase.domain.repositories.requisition_repository import (
    RequisitionRepository,
)


class ListRequisitionsUseCase:
    def __init__(
        self,
        requisition_repository: RequisitionRepository,
    ) -> None:
        self._requisition_repository = requisition_repository

    def execute(
        self,
        query: ListRequisitionsQuery,
    ) -> list[PurchaseRequisition]:
        business_id = self._validate_positive_id(
            query.business_id,
            "Business ID",
        )
        status = self._validate_status(query.status)
        requested_by_id = self._validate_optional_positive_id(
            query.requested_by_id,
            "Requested by ID",
        )

        return self._requisition_repository.list(
            business_id,
            status=status,
            requested_by_id=requested_by_id,
        )

    @staticmethod
    def _validate_positive_id(value: int, field_name: str) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")

        return value

    @classmethod
    def _validate_optional_positive_id(
        cls,
        value: int | None,
        field_name: str,
    ) -> int | None:
        if value is None:
            return None

        return cls._validate_positive_id(value, field_name)

    @staticmethod
    def _validate_status(
        status: RequisitionStatus | None,
    ) -> RequisitionStatus | None:
        if status is not None and not isinstance(status, RequisitionStatus):
            raise ValueError("Status must be a requisition status or None.")

        return status
