from collections import defaultdict
from decimal import Decimal

from purchase.application.dto.requisition_order_summary import (
    RequisitionOrderSummaryDTO,
    RequisitionOrderSummaryItemDTO,
)
from purchase.domain.enums.purchase_order_status import PurchaseOrderStatus
from purchase.domain.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)
from purchase.domain.repositories.requisition_repository import (
    RequisitionRepository,
)


class GetRequisitionOrderSummaryUseCase:
    def __init__(
        self,
        requisition_repository: RequisitionRepository,
        purchase_order_repository: PurchaseOrderRepository,
    ) -> None:
        self._requisition_repository = requisition_repository
        self._purchase_order_repository = purchase_order_repository

    def execute(
        self,
        requisition_id: int,
        business_id: int,
    ) -> RequisitionOrderSummaryDTO:
        self._validate_positive_id(requisition_id, "Requisition ID")
        self._validate_positive_id(business_id, "Business ID")

        requisition = self._requisition_repository.get_by_id_for_business(
            requisition_id,
            business_id,
        )
        if requisition is None:
            raise ValueError("Requisition does not exist in this business.")

        requested: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
        for item in requisition.items:
            requested[item.ingredient_id] += item.quantity

        ordered: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
        purchase_orders = self._purchase_order_repository.list(
            business_id,
            requisition_id=requisition_id,
        )
        for purchase_order in purchase_orders:
            if purchase_order.status == PurchaseOrderStatus.CANCELLED:
                continue
            for item in purchase_order.items:
                ordered[item.ingredient_id] += item.quantity

        summary_items = [
            RequisitionOrderSummaryItemDTO(
                ingredient_id=ingredient_id,
                requested_quantity=requested_quantity,
                ordered_quantity=ordered[ingredient_id],
                remaining_quantity=max(
                    requested_quantity - ordered[ingredient_id],
                    Decimal("0"),
                ),
            )
            for ingredient_id, requested_quantity in requested.items()
        ]

        return RequisitionOrderSummaryDTO(
            requisition_id=requisition.id,
            business_id=requisition.business_id,
            status=requisition.status,
            items=summary_items,
        )

    @staticmethod
    def _validate_positive_id(value: int, field_name: str) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")
