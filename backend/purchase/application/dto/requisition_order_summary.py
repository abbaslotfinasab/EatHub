from dataclasses import dataclass
from decimal import Decimal

from purchase.domain.enums.requisition_status import RequisitionStatus


@dataclass(frozen=True)
class RequisitionOrderSummaryItemDTO:
    ingredient_id: int
    requested_quantity: Decimal
    ordered_quantity: Decimal
    remaining_quantity: Decimal


@dataclass(frozen=True)
class RequisitionOrderSummaryDTO:
    requisition_id: int
    business_id: int
    status: RequisitionStatus
    items: list[RequisitionOrderSummaryItemDTO]
