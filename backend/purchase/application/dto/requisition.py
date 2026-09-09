from dataclasses import dataclass
from decimal import Decimal

from purchase.domain.enums.requisition_status import RequisitionStatus


@dataclass(frozen=True)
class CreateRequisitionItemDTO:
    ingredient_id: int
    quantity: Decimal
    note: str = ""


@dataclass(frozen=True)
class CreateRequisitionDTO:
    business_id: int
    requested_by_id: int
    items: list[CreateRequisitionItemDTO]
    reason: str = ""


@dataclass(frozen=True)
class ListRequisitionsQuery:
    business_id: int
    status: RequisitionStatus | None = None
    requested_by_id: int | None = None
