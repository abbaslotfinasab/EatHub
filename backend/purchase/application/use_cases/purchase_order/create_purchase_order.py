from datetime import date
from decimal import Decimal

from purchase.application.dto.purchase_order import CreatePurchaseOrderDTO
from purchase.domain.entities.purchase_order import (
    PurchaseOrder,
    PurchaseOrderItem,
)
from purchase.domain.enums.requisition_status import RequisitionStatus
from purchase.domain.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)
from purchase.domain.repositories.requisition_repository import (
    RequisitionRepository,
)
from purchase.domain.repositories.supplier_repository import (
    SupplierRepository,
)


class CreatePurchaseOrderUseCase:
    def __init__(
        self,
        purchase_order_repository: PurchaseOrderRepository,
        supplier_repository: SupplierRepository,
        requisition_repository: RequisitionRepository | None = None,
    ) -> None:
        self._purchase_order_repository = purchase_order_repository
        self._supplier_repository = supplier_repository
        self._requisition_repository = requisition_repository

    def execute(self, command: CreatePurchaseOrderDTO) -> PurchaseOrder:
        business_id = self._validate_positive_id(command.business_id, "Business ID")
        supplier_id = self._validate_positive_id(command.supplier_id, "Supplier ID")
        order_date = self._validate_date(command.order_date, "Order date")
        expected_date = self._validate_optional_date(
            command.expected_date,
            "Expected date",
        )
        items = self._create_items(command.items)
        discount = self._validate_decimal(command.discount, "Discount")
        tax = self._validate_decimal(command.tax, "Tax")

        supplier = self._supplier_repository.get_by_id_for_business(
            supplier_id,
            business_id,
        )
        if supplier is None:
            raise ValueError("Supplier does not exist in this business.")

        requisition_id = self._validate_requisition(
            business_id,
            command.requisition_id,
        )

        purchase_order = PurchaseOrder(
            id=None,
            business_id=business_id,
            supplier_id=supplier_id,
            requisition_id=requisition_id,
            order_date=order_date,
            expected_date=expected_date,
            discount=discount,
            tax=tax,
            items=items,
        )

        return self._purchase_order_repository.save(purchase_order)

    def _validate_requisition(
        self,
        business_id: int,
        requisition_id: int | None,
    ) -> int | None:
        if requisition_id is None:
            return None

        validated_requisition_id = self._validate_positive_id(
            requisition_id,
            "Requisition ID",
        )
        if self._requisition_repository is None:
            raise ValueError(
                "Requisition repository is required when a requisition is supplied."
            )

        requisition = self._requisition_repository.get_by_id_for_business(
            validated_requisition_id,
            business_id,
        )
        if requisition is None:
            raise ValueError("Requisition does not exist in this business.")

        if requisition.status != RequisitionStatus.APPROVED:
            raise ValueError("Requisition must be approved before creating an order.")

        if self._purchase_order_repository.exists_by_requisition(
            business_id,
            validated_requisition_id,
        ):
            raise ValueError(
                "A purchase order already exists for this requisition."
            )

        return validated_requisition_id

    @classmethod
    def _create_items(cls, commands: list) -> list[PurchaseOrderItem]:
        return [
            PurchaseOrderItem(
                ingredient_id=cls._validate_positive_id(
                    item.ingredient_id,
                    "Ingredient ID",
                ),
                quantity=cls._validate_positive_decimal(
                    item.quantity,
                    "Quantity",
                ),
                unit_price=cls._validate_non_negative_decimal(
                    item.unit_price,
                    "Unit price",
                ),
            )
            for item in commands
        ]

    @staticmethod
    def _validate_positive_id(value: int, field_name: str) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")
        return value

    @staticmethod
    def _validate_date(value: date, field_name: str) -> date:
        if not isinstance(value, date):
            raise ValueError(f"{field_name} must be a date.")
        return value

    @classmethod
    def _validate_optional_date(
        cls,
        value: date | None,
        field_name: str,
    ) -> date | None:
        if value is None:
            return None
        return cls._validate_date(value, field_name)

    @staticmethod
    def _validate_decimal(value: Decimal, field_name: str) -> Decimal:
        if not isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be a decimal.")
        return value

    @classmethod
    def _validate_positive_decimal(
        cls,
        value: Decimal,
        field_name: str,
    ) -> Decimal:
        value = cls._validate_decimal(value, field_name)
        if value <= 0:
            raise ValueError(f"{field_name} must be greater than zero.")
        return value

    @classmethod
    def _validate_non_negative_decimal(
        cls,
        value: Decimal,
        field_name: str,
    ) -> Decimal:
        value = cls._validate_decimal(value, field_name)
        if value < 0:
            raise ValueError(f"{field_name} cannot be negative.")
        return value
