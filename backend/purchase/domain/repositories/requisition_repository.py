

from abc import ABC, abstractmethod

from purchase.domain.entities.requisition import (
    PurchaseRequisitionDecision,
    PurchaseRequisition,
)
from purchase.domain.enums.requisition_status import (
    RequisitionStatus,
)


class RequisitionRepository(ABC):

    @abstractmethod
    def get_by_id_for_business(
        self,
        requisition_id: int,
        business_id: int,
    ) -> PurchaseRequisition | None:
        raise NotImplementedError

    @abstractmethod
    def list(
        self,
        business_id: int,
        *,
        status: RequisitionStatus | None = None,
        requested_by_id: int | None = None,
    ) -> list[PurchaseRequisition]:
        raise NotImplementedError

    @abstractmethod
    def save(
        self,
        requisition: PurchaseRequisition,
    ) -> PurchaseRequisition:
        raise NotImplementedError

    @abstractmethod
    def record_decision(
        self,
        requisition_id: int,
        business_id: int,
        actor_id: int,
        decision: str,
        rejection_reason: str | None = None,
    ) -> PurchaseRequisition:
        raise NotImplementedError

    @abstractmethod
    def list_decisions_for_business(
        self,
        requisition_id: int,
        business_id: int,
    ) -> list[PurchaseRequisitionDecision]:
        raise NotImplementedError

