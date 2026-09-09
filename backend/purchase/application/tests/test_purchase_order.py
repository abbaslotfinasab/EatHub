from datetime import date
from decimal import Decimal
from unittest import TestCase

from purchase.application.dto.purchase_order import (
    CreatePurchaseOrderDTO,
    CreatePurchaseOrderItemDTO,
    UpdatePurchaseOrderDTO,
)
from purchase.application.use_cases.purchase_order.cancel_purchase_order import (
    CancelPurchaseOrderUseCase,
)
from purchase.application.use_cases.purchase_order.create_purchase_order import (
    CreatePurchaseOrderUseCase,
)
from purchase.application.use_cases.purchase_order.get_purchase_order import (
    GetPurchaseOrderUseCase,
)
from purchase.application.use_cases.purchase_order.send_purchase_order import (
    SendPurchaseOrderUseCase,
)
from purchase.application.use_cases.purchase_order.update_purchase_order import (
    UpdatePurchaseOrderUseCase,
)
from purchase.domain.entities.purchase_order import PurchaseOrder
from purchase.domain.entities.requisition import PurchaseRequisition
from purchase.domain.entities.supplier import Supplier
from purchase.domain.enums.requisition_status import RequisitionStatus


class FakePurchaseOrderRepository:
    def __init__(self) -> None:
        self.orders: dict[int, PurchaseOrder] = {}
        self.next_id = 1

    def get_by_id_for_business(
        self,
        purchase_order_id: int,
        business_id: int,
    ) -> PurchaseOrder | None:
        order = self.orders.get(purchase_order_id)
        if order is None or order.business_id != business_id:
            return None
        return order

    def list(self, business_id: int, **kwargs: object) -> list[PurchaseOrder]:
        return [
            order
            for order in self.orders.values()
            if order.business_id == business_id
        ]

    def save(self, purchase_order: PurchaseOrder) -> PurchaseOrder:
        if purchase_order.id is None:
            purchase_order.id = self.next_id
            self.next_id += 1
        self.orders[purchase_order.id] = purchase_order
        return purchase_order

    def exists_by_requisition(self, business_id: int, requisition_id: int) -> bool:
        return any(
            order.business_id == business_id
            and order.requisition_id == requisition_id
            for order in self.orders.values()
        )


class FakeSupplierRepository:
    def __init__(self, suppliers: list[Supplier]) -> None:
        self.suppliers = {supplier.id: supplier for supplier in suppliers}

    def get_by_id_for_business(
        self,
        supplier_id: int,
        business_id: int,
    ) -> Supplier | None:
        supplier = self.suppliers.get(supplier_id)
        if supplier is None or supplier.business_id != business_id:
            return None
        return supplier


class FakeRequisitionRepository:
    def __init__(self, requisitions: list[PurchaseRequisition]) -> None:
        self.requisitions = {
            requisition.id: requisition for requisition in requisitions
        }

    def get_by_id_for_business(
        self,
        requisition_id: int,
        business_id: int,
    ) -> PurchaseRequisition | None:
        requisition = self.requisitions.get(requisition_id)
        if requisition is None or requisition.business_id != business_id:
            return None
        return requisition


class PurchaseOrderApplicationTests(TestCase):
    def setUp(self) -> None:
        self.purchase_order_repository = FakePurchaseOrderRepository()
        self.supplier_repository = FakeSupplierRepository([
            Supplier(id=1, business_id=1, name="Local Supplier"),
            Supplier(id=2, business_id=2, name="Other Supplier"),
        ])
        self.requisition_repository = FakeRequisitionRepository([
            PurchaseRequisition(
                id=1,
                business_id=1,
                requested_by_id=1,
                status=RequisitionStatus.APPROVED,
            ),
            PurchaseRequisition(
                id=2,
                business_id=1,
                requested_by_id=1,
                status=RequisitionStatus.DRAFT,
            ),
            PurchaseRequisition(
                id=3,
                business_id=2,
                requested_by_id=2,
                status=RequisitionStatus.APPROVED,
            ),
        ])
        self.create_use_case = CreatePurchaseOrderUseCase(
            self.purchase_order_repository,
            self.supplier_repository,
            self.requisition_repository,
        )

    def create_command(self, **kwargs: object) -> CreatePurchaseOrderDTO:
        values = {
            "business_id": 1,
            "supplier_id": 1,
            "order_date": date(2026, 9, 7),
            "items": [
                CreatePurchaseOrderItemDTO(
                    ingredient_id=1,
                    quantity=Decimal("2"),
                    unit_price=Decimal("3"),
                )
            ],
        }
        values.update(kwargs)
        return CreatePurchaseOrderDTO(**values)

    def test_create_purchase_order_with_valid_supplier_and_items(self) -> None:
        order = self.create_use_case.execute(self.create_command())

        self.assertEqual(order.business_id, 1)
        self.assertEqual(order.supplier_id, 1)
        self.assertEqual(order.total_amount(), Decimal("6"))

    def test_rejects_supplier_from_another_business(self) -> None:
        with self.assertRaises(ValueError):
            self.create_use_case.execute(self.create_command(supplier_id=2))

    def test_create_purchase_order_with_approved_requisition(self) -> None:
        order = self.create_use_case.execute(self.create_command(requisition_id=1))

        self.assertEqual(order.requisition_id, 1)

    def test_rejects_requisition_from_another_business(self) -> None:
        with self.assertRaises(ValueError):
            self.create_use_case.execute(self.create_command(requisition_id=3))

    def test_rejects_requisition_that_is_not_approved(self) -> None:
        with self.assertRaises(ValueError):
            self.create_use_case.execute(self.create_command(requisition_id=2))

    def test_update_draft_purchase_order(self) -> None:
        order = self.create_use_case.execute(self.create_command())

        updated = UpdatePurchaseOrderUseCase(
            self.purchase_order_repository
        ).execute(
            UpdatePurchaseOrderDTO(
                business_id=1,
                purchase_order_id=order.id,
                items=[
                    CreatePurchaseOrderItemDTO(
                        ingredient_id=2,
                        quantity=Decimal("3"),
                        unit_price=Decimal("4"),
                    )
                ],
                discount=Decimal("1"),
                tax=Decimal("2"),
            )
        )

        self.assertEqual([item.ingredient_id for item in updated.items], [2])
        self.assertEqual(updated.total_amount(), Decimal("13"))

    def test_send_purchase_order(self) -> None:
        order = self.create_use_case.execute(self.create_command())

        sent = SendPurchaseOrderUseCase(
            self.purchase_order_repository
        ).execute(order.id, business_id=1)

        self.assertEqual(sent.status, "sent")

    def test_cancel_purchase_order(self) -> None:
        order = self.create_use_case.execute(self.create_command())

        cancelled = CancelPurchaseOrderUseCase(
            self.purchase_order_repository
        ).execute(order.id, business_id=1)

        self.assertEqual(cancelled.status, "cancelled")

    def test_rejects_invalid_lifecycle_transition(self) -> None:
        order = self.create_use_case.execute(self.create_command())
        send_use_case = SendPurchaseOrderUseCase(self.purchase_order_repository)
        send_use_case.execute(order.id, business_id=1)

        with self.assertRaises(ValueError):
            send_use_case.execute(order.id, business_id=1)

    def test_cross_business_get_is_rejected(self) -> None:
        order = self.create_use_case.execute(self.create_command())

        with self.assertRaises(ValueError):
            GetPurchaseOrderUseCase(self.purchase_order_repository).execute(
                order.id,
                business_id=2,
            )

    def test_cross_business_update_cannot_change_ownership(self) -> None:
        order = self.create_use_case.execute(self.create_command())

        with self.assertRaises(ValueError):
            UpdatePurchaseOrderUseCase(
                self.purchase_order_repository
            ).execute(
                UpdatePurchaseOrderDTO(
                    business_id=2,
                    purchase_order_id=order.id,
                    items=[],
                )
            )

        self.assertEqual(order.business_id, 1)
