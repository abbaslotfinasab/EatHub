from datetime import date

from purchase.application.dto.purchase_order import ListPurchaseOrdersQuery
from purchase.domain.entities.purchase_order import PurchaseOrder
from purchase.domain.enums.purchase_order_status import PurchaseOrderStatus
from purchase.domain.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)


class ListPurchaseOrdersUseCase:
    def __init__(self, purchase_order_repository: PurchaseOrderRepository) -> None:
        self._purchase_order_repository = purchase_order_repository

    def execute(self, query: ListPurchaseOrdersQuery) -> list[PurchaseOrder]:
        business_id = self._validate_positive_id(query.business_id, "Business ID")
        status = self._validate_status(query.status)
        supplier_id = self._validate_optional_positive_id(
            query.supplier_id,
            "Supplier ID",
        )
        requisition_id = self._validate_optional_positive_id(
            query.requisition_id,
            "Requisition ID",
        )
        order_date_from = self._validate_optional_date(
            query.order_date_from,
            "Order date from",
        )
        order_date_to = self._validate_optional_date(
            query.order_date_to,
            "Order date to",
        )

        if (
            order_date_from is not None
            and order_date_to is not None
            and order_date_from > order_date_to
        ):
            raise ValueError("Order date from cannot be after order date to.")

        return self._purchase_order_repository.list(
            business_id,
            status=status,
            supplier_id=supplier_id,
            requisition_id=requisition_id,
            order_date_from=order_date_from,
            order_date_to=order_date_to,
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
        status: PurchaseOrderStatus | None,
    ) -> PurchaseOrderStatus | None:
        if status is not None and not isinstance(status, PurchaseOrderStatus):
            raise ValueError("Status must be a purchase order status or None.")
        return status

    @staticmethod
    def _validate_optional_date(
        value: date | None,
        field_name: str,
    ) -> date | None:
        if value is not None and not isinstance(value, date):
            raise ValueError(f"{field_name} must be a date or None.")
        return value
