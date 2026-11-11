from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.enums import RoleCode
from accounts.models import Business, Membership, Role, RolePermission, User
from accounts.services.rbac_initializer import RBACInitializer
from core.enums import PermissionCode
from inventory.models import Ingredient
from purchase.models import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequisition,
    PurchaseRequisitionItem,
    Supplier,
)


class RequisitionOrderSummaryAPITests(APITestCase):
    endpoint = "/api/purchase/requisitions/"

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="summary-requester@example.com",
            password="password",
            name="Summary Requester",
            number="7101",
        )
        self.other_user = User.objects.create_user(
            email="summary-other@example.com",
            password="password",
            name="Other Requester",
            number="7102",
        )
        self.business = Business.objects.create(name="Summary Business")
        self.other_business = Business.objects.create(name="Other Summary Business")
        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            code=RoleCode.OWNER,
            is_system=True,
        )
        self.other_role = Role.objects.create(
            business=self.other_business,
            name="Owner",
            code=RoleCode.OWNER,
            is_system=True,
        )
        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=self.role,
            is_active=True,
        )
        Membership.objects.create(
            user=self.other_user,
            business=self.other_business,
            role=self.other_role,
            is_active=True,
        )
        RBACInitializer.initialize(self.business)
        RBACInitializer.initialize(self.other_business)
        self.ingredient = Ingredient.objects.create(
            business=self.business,
            name="Summary Flour",
            unit=Ingredient.Unit.KG,
        )
        self.other_ingredient = Ingredient.objects.create(
            business=self.other_business,
            name="Other Summary Flour",
            unit=Ingredient.Unit.KG,
        )
        self.supplier = Supplier.objects.create(
            business=self.business,
            name="Summary Supplier",
        )
        self.client.force_authenticate(self.user)

    def summary_endpoint(self, requisition_id: int) -> str:
        return f"{self.endpoint}{requisition_id}/order-summary/"

    def create_requisition(
        self,
        *,
        business: Business | None = None,
        requester: User | None = None,
        ingredient: Ingredient | None = None,
        status_value: str = PurchaseRequisition.Status.APPROVED,
    ) -> PurchaseRequisition:
        requisition = PurchaseRequisition.objects.create(
            business=business or self.business,
            requested_by=requester or self.user,
            status=status_value,
            reason="Order summary test",
        )
        PurchaseRequisitionItem.objects.create(
            requisition=requisition,
            ingredient=ingredient or self.ingredient,
            quantity=Decimal("2.000"),
            note="First line",
        )
        PurchaseRequisitionItem.objects.create(
            requisition=requisition,
            ingredient=ingredient or self.ingredient,
            quantity=Decimal("1.500"),
            note="Duplicate ingredient line",
        )
        return requisition

    def add_order(
        self,
        requisition: PurchaseRequisition,
        *,
        quantity: str,
        order_status: str,
    ) -> PurchaseOrder:
        order = PurchaseOrder.objects.create(
            business=requisition.business,
            supplier=(
                self.supplier
                if requisition.business_id == self.business.id
                else Supplier.objects.create(
                    business=requisition.business,
                    name=f"Supplier {requisition.business_id}",
                )
            ),
            requisition=requisition,
            order_date=date(2026, 11, 11),
            status=order_status,
        )
        PurchaseOrderItem.objects.create(
            purchase_order=order,
            ingredient=requisition.items.first().ingredient,
            quantity=Decimal(quantity),
            unit_price=Decimal("3.00"),
        )
        return order

    def test_summary_aggregates_duplicate_lines_and_active_orders(self) -> None:
        requisition = self.create_requisition()
        self.add_order(
            requisition,
            quantity="1.250",
            order_status=PurchaseOrder.Status.DRAFT,
        )
        self.add_order(
            requisition,
            quantity="0.500",
            order_status=PurchaseOrder.Status.SENT,
        )
        self.add_order(
            requisition,
            quantity="0.250",
            order_status=PurchaseOrder.Status.RECEIVED,
        )
        self.add_order(
            requisition,
            quantity="3.000",
            order_status=PurchaseOrder.Status.CANCELLED,
        )

        response = self.client.get(self.summary_endpoint(requisition.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["requisition_id"], requisition.id)
        self.assertEqual(response.data["business_id"], self.business.id)
        self.assertEqual(response.data["status"], "approved")
        self.assertEqual(
            response.data["items"],
            [{
                "ingredient_id": self.ingredient.id,
                "requested_quantity": "3.500",
                "ordered_quantity": "2.000",
                "remaining_quantity": "1.500",
            }],
        )

    def test_summary_returns_zero_ordered_for_unordered_ingredient(self) -> None:
        requisition = self.create_requisition()

        response = self.client.get(self.summary_endpoint(requisition.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["items"][0]["ordered_quantity"], "0.000")
        self.assertEqual(response.data["items"][0]["remaining_quantity"], "3.500")

    def test_summary_never_returns_negative_remaining_for_legacy_overage(self) -> None:
        requisition = self.create_requisition()
        self.add_order(
            requisition,
            quantity="4.000",
            order_status=PurchaseOrder.Status.SENT,
        )

        response = self.client.get(self.summary_endpoint(requisition.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["items"][0]["ordered_quantity"], "4.000")
        self.assertEqual(response.data["items"][0]["remaining_quantity"], "0.000")

    def test_cross_business_requisition_is_not_found(self) -> None:
        requisition = self.create_requisition(
            business=self.other_business,
            requester=self.other_user,
            ingredient=self.other_ingredient,
        )

        response = self.client.get(self.summary_endpoint(requisition.id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_own_read_permission_hides_another_requesters_summary(self) -> None:
        another_user = User.objects.create_user(
            email="summary-same-business@example.com",
            password="password",
            name="Same Business Requester",
            number="7103",
        )
        Membership.objects.create(
            user=another_user,
            business=self.business,
            role=self.role,
            is_active=True,
        )
        requisition = self.create_requisition(requester=another_user)
        RolePermission.objects.filter(
            role=self.role,
            permission__code=PermissionCode.PURCHASE_VIEW.value,
        ).delete()

        response = self.client.get(self.summary_endpoint(requisition.id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_summary_requires_read_permission(self) -> None:
        RolePermission.objects.filter(
            role=self.role,
            permission__code__in=[
                PermissionCode.PURCHASE_VIEW.value,
                PermissionCode.PURCHASE_REQUISITION_VIEW_OWN.value,
            ],
        ).delete()
        requisition = self.create_requisition()

        response = self.client.get(self.summary_endpoint(requisition.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_summary_is_rejected(self) -> None:
        requisition = self.create_requisition()
        self.client.force_authenticate(user=None)

        response = self.client.get(self.summary_endpoint(requisition.id))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
