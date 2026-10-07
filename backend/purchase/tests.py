from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.enums import RoleCode
from accounts.models import Business, Membership, Role, User
from purchase.domain.entities.supplier import Supplier
from purchase.domain.entities.requisition import (
    PurchaseRequisition,
    PurchaseRequisitionItem,
)
from purchase.domain.enums.requisition_status import RequisitionStatus
from purchase.domain.entities.purchase_order import (
    PurchaseOrder,
    PurchaseOrderItem,
)
from purchase.domain.enums.purchase_order_status import PurchaseOrderStatus
from purchase.infrastructure.persistence.django.repositories.purchase_order_repository import (
    DjangoPurchaseOrderRepository,
)
from purchase.infrastructure.persistence.django.repositories.requisition_repository import (
    DjangoRequisitionRepository,
)
from purchase.infrastructure.persistence.django.repositories.supplier_repository import (
    DjangoSupplierRepository,
)
from purchase.models import (
    PurchaseOrder as DjangoPurchaseOrder,
    PurchaseOrderItem as DjangoPurchaseOrderItem,
    PurchaseRequisition as DjangoPurchaseRequisition,
    PurchaseRequisitionItem as DjangoPurchaseRequisitionItem,
    Supplier as DjangoSupplier,
)
from inventory.models import Ingredient


class DjangoSupplierRepositoryTests(TestCase):
    def setUp(self) -> None:
        self.business_1 = Business.objects.create(name="Business One")
        self.business_2 = Business.objects.create(name="Business Two")
        self.repository = DjangoSupplierRepository()

    def create_supplier(
        self,
        business_id: int,
        name: str,
        **kwargs: object,
    ) -> Supplier:
        return self.repository.save(
            Supplier(
                id=None,
                business_id=business_id,
                name=name,
                **kwargs,
            )
        )

    def test_save_creates_supplier(self) -> None:
        supplier = self.create_supplier(
            self.business_1.id,
            "Test Supplier",
            phone="123",
        )

        model = DjangoSupplier.objects.get(id=supplier.id)

        self.assertEqual(model.business_id, self.business_1.id)
        self.assertEqual(model.name, "Test Supplier")
        self.assertEqual(supplier.business_id, self.business_1.id)
        self.assertEqual(supplier.phone, "123")

    def test_get_by_id_for_business_returns_supplier(self) -> None:
        supplier = self.create_supplier(
            self.business_1.id,
            "Test Supplier",
        )

        result = self.repository.get_by_id_for_business(
            supplier.id,
            self.business_1.id,
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.id, supplier.id)
        self.assertEqual(result.business_id, self.business_1.id)

    def test_get_by_id_for_business_hides_other_business_supplier(self) -> None:
        supplier = self.create_supplier(
            self.business_1.id,
            "Test Supplier",
        )

        result = self.repository.get_by_id_for_business(
            supplier.id,
            self.business_2.id,
        )

        self.assertIsNone(result)

    def test_list_search_is_tenant_scoped(self) -> None:
        supplier_1 = self.create_supplier(
            self.business_1.id,
            "Restaurant Supplier ABC",
        )
        self.create_supplier(
            self.business_2.id,
            "Restaurant Supplier ABC",
        )

        result = self.repository.list(
            self.business_1.id,
            search="Supplier ABC",
        )

        self.assertEqual([supplier.id for supplier in result], [supplier_1.id])

    def test_list_filters_by_active_status(self) -> None:
        active_supplier = self.create_supplier(
            self.business_1.id,
            "Active Supplier",
        )
        self.create_supplier(
            self.business_1.id,
            "Inactive Supplier",
            is_active=False,
        )

        result = self.repository.list(
            self.business_1.id,
            is_active=True,
        )

        self.assertEqual([supplier.id for supplier in result], [active_supplier.id])

    def test_exists_by_name_is_tenant_scoped_and_supports_exclusion(self) -> None:
        supplier_1 = self.create_supplier(self.business_1.id, "ABC")
        self.create_supplier(self.business_2.id, "ABC")

        self.assertTrue(
            self.repository.exists_by_name(self.business_1.id, "ABC")
        )
        self.assertTrue(
            self.repository.exists_by_name(self.business_2.id, "ABC")
        )
        self.assertFalse(
            self.repository.exists_by_name(
                self.business_1.id,
                "ABC",
                exclude_id=supplier_1.id,
            )
        )

    def test_save_updates_mutable_fields(self) -> None:
        supplier = self.create_supplier(self.business_1.id, "Original")
        supplier.name = "Updated"
        supplier.phone = "123"
        supplier.email = "supplier@example.com"
        supplier.address = "Address"
        supplier.tax_number = "TAX-1"
        supplier.notes = "Notes"
        supplier.is_active = False

        result = self.repository.save(supplier)
        model = DjangoSupplier.objects.get(id=supplier.id)

        self.assertEqual(result.name, "Updated")
        self.assertEqual(model.name, "Updated")
        self.assertEqual(model.phone, "123")
        self.assertEqual(model.email, "supplier@example.com")
        self.assertEqual(model.address, "Address")
        self.assertEqual(model.tax_number, "TAX-1")
        self.assertEqual(model.notes, "Notes")
        self.assertFalse(model.is_active)

    def test_save_rejects_cross_business_update(self) -> None:
        supplier = self.create_supplier(self.business_1.id, "Test Supplier")
        malicious_supplier = Supplier(
            id=supplier.id,
            business_id=self.business_2.id,
            name="Moved Supplier",
        )

        with self.assertRaises(ValueError):
            self.repository.save(malicious_supplier)

        model = DjangoSupplier.objects.get(id=supplier.id)
        self.assertEqual(model.business_id, self.business_1.id)
        self.assertEqual(model.name, "Test Supplier")


class DjangoRequisitionRepositoryTests(TestCase):
    def setUp(self) -> None:
        self.business_1 = Business.objects.create(name="Business One")
        self.business_2 = Business.objects.create(name="Business Two")
        self.user_1 = User.objects.create_user(
            email="requester-one@example.com",
            password="password",
            name="Requester One",
            number="2001",
        )
        self.user_2 = User.objects.create_user(
            email="requester-two@example.com",
            password="password",
            name="Requester Two",
            number="2002",
        )
        self.ingredient_1 = self.create_ingredient(
            self.business_1,
            "Ingredient One",
        )
        self.ingredient_2 = self.create_ingredient(
            self.business_1,
            "Ingredient Two",
        )
        self.other_ingredient = self.create_ingredient(
            self.business_2,
            "Other Ingredient",
        )
        self.repository = DjangoRequisitionRepository()

    @staticmethod
    def create_ingredient(business: Business, name: str) -> Ingredient:
        return Ingredient.objects.create(
            business=business,
            name=name,
            unit=Ingredient.Unit.KG,
        )

    def create_requisition(
        self,
        *,
        business_id: int | None = None,
        requested_by_id: int | None = None,
        status: RequisitionStatus = RequisitionStatus.DRAFT,
        reason: str = "Stock replenishment",
        items: list[PurchaseRequisitionItem] | None = None,
    ) -> PurchaseRequisition:
        return self.repository.save(
            PurchaseRequisition(
                id=None,
                business_id=business_id or self.business_1.id,
                requested_by_id=requested_by_id or self.user_1.id,
                status=status,
                reason=reason,
                items=items
                or [
                    PurchaseRequisitionItem(
                        ingredient_id=self.ingredient_1.id,
                        quantity=1,
                        note="Needed",
                    )
                ],
            )
        )

    def test_save_creates_requisition_with_multiple_items(self) -> None:
        requisition = self.create_requisition(
            items=[
                PurchaseRequisitionItem(self.ingredient_1.id, 1, "First"),
                PurchaseRequisitionItem(self.ingredient_2.id, 2, "Second"),
            ]
        )

        model = DjangoPurchaseRequisition.objects.get(id=requisition.id)
        self.assertEqual(model.business_id, self.business_1.id)
        self.assertEqual(model.requested_by_id, self.user_1.id)
        self.assertEqual(model.items.count(), 2)
        self.assertEqual([item.ingredient_id for item in requisition.items], [
            self.ingredient_1.id,
            self.ingredient_2.id,
        ])

    def test_get_by_id_for_business_loads_complete_aggregate(self) -> None:
        requisition = self.create_requisition(
            items=[
                PurchaseRequisitionItem(self.ingredient_1.id, 1, "First"),
                PurchaseRequisitionItem(self.ingredient_2.id, 2, "Second"),
            ]
        )

        result = self.repository.get_by_id_for_business(
            requisition.id,
            self.business_1.id,
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.reason, requisition.reason)
        self.assertEqual(
            [(item.ingredient_id, item.quantity, item.note) for item in result.items],
            [
                (self.ingredient_1.id, 1, "First"),
                (self.ingredient_2.id, 2, "Second"),
            ],
        )

    def test_get_by_id_for_business_hides_other_business_requisition(self) -> None:
        requisition = self.create_requisition()

        self.assertIsNone(self.repository.get_by_id_for_business(
            requisition.id,
            self.business_2.id,
        ))

    def test_list_is_tenant_scoped_and_supports_filters(self) -> None:
        draft = self.create_requisition(reason="Draft")
        submitted = self.create_requisition(
            status=RequisitionStatus.SUBMITTED,
            requested_by_id=self.user_2.id,
            reason="Submitted",
        )
        self.create_requisition(
            business_id=self.business_2.id,
            reason="Other business",
            items=[PurchaseRequisitionItem(self.other_ingredient.id, 1)],
        )

        self.assertEqual(
            [item.id for item in self.repository.list(self.business_1.id)],
            [draft.id, submitted.id],
        )
        self.assertEqual(
            [item.id for item in self.repository.list(
                self.business_1.id,
                status=RequisitionStatus.SUBMITTED,
            )],
            [submitted.id],
        )
        self.assertEqual(
            [item.id for item in self.repository.list(
                self.business_1.id,
                requested_by_id=self.user_2.id,
            )],
            [submitted.id],
        )

    def test_save_existing_updates_root_and_replaces_item_collection(self) -> None:
        requisition = self.create_requisition(
            items=[PurchaseRequisitionItem(self.ingredient_1.id, 1, "Old")]
        )
        stale_item_id = DjangoPurchaseRequisitionItem.objects.get(
            requisition_id=requisition.id,
        ).id
        requisition.requested_by_id = self.user_2.id
        requisition.status = RequisitionStatus.SUBMITTED
        requisition.reason = "Updated reason"
        requisition.items = [
            PurchaseRequisitionItem(self.ingredient_2.id, 3, "Replacement"),
            PurchaseRequisitionItem(self.ingredient_1.id, 4, "Added back"),
        ]

        result = self.repository.save(requisition)
        model = DjangoPurchaseRequisition.objects.get(id=requisition.id)
        items = list(model.items.order_by("id"))

        self.assertEqual(result.status, RequisitionStatus.SUBMITTED)
        self.assertEqual(model.requested_by_id, self.user_2.id)
        self.assertEqual(model.reason, "Updated reason")
        self.assertFalse(DjangoPurchaseRequisitionItem.objects.filter(
            id=stale_item_id,
        ).exists())
        self.assertEqual(
            [(item.ingredient_id, item.quantity, item.note) for item in items],
            [
                (self.ingredient_2.id, 3, "Replacement"),
                (self.ingredient_1.id, 4, "Added back"),
            ],
        )

    def test_save_preserves_business_id(self) -> None:
        requisition = self.create_requisition()
        requisition.reason = "Updated"

        self.repository.save(requisition)

        self.assertEqual(
            DjangoPurchaseRequisition.objects.get(id=requisition.id).business_id,
            self.business_1.id,
        )

    def test_save_rejects_cross_business_update(self) -> None:
        requisition = self.create_requisition()
        malicious_requisition = PurchaseRequisition(
            id=requisition.id,
            business_id=self.business_2.id,
            requested_by_id=self.user_2.id,
            reason="Moved",
            items=[PurchaseRequisitionItem(self.other_ingredient.id, 1)],
        )

        with self.assertRaises(ValueError):
            self.repository.save(malicious_requisition)

        model = DjangoPurchaseRequisition.objects.get(id=requisition.id)
        self.assertEqual(model.business_id, self.business_1.id)
        self.assertEqual(model.reason, requisition.reason)

    def test_save_rejects_other_business_ingredient_without_partial_writes(self) -> None:
        requisition = self.create_requisition()
        original_reason = requisition.reason
        original_item_count = DjangoPurchaseRequisitionItem.objects.filter(
            requisition_id=requisition.id,
        ).count()
        requisition.reason = "Should not persist"
        requisition.items = [
            PurchaseRequisitionItem(self.ingredient_1.id, 2),
            PurchaseRequisitionItem(self.other_ingredient.id, 3),
        ]

        with self.assertRaises(ValueError):
            self.repository.save(requisition)

        model = DjangoPurchaseRequisition.objects.get(id=requisition.id)
        self.assertEqual(model.reason, original_reason)
        self.assertEqual(model.items.count(), original_item_count)

    def test_save_accepts_ingredient_from_same_business(self) -> None:
        requisition = self.create_requisition(
            items=[PurchaseRequisitionItem(self.ingredient_2.id, 2, "Valid")]
        )

        self.assertEqual(requisition.items[0].ingredient_id, self.ingredient_2.id)


class SupplierAPITests(APITestCase):
    endpoint = "/api/purchase/suppliers/"

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="password",
            name="Owner",
            number="1001",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="password",
            name="Other Owner",
            number="1002",
        )

        self.business = Business.objects.create(name="Business One")
        self.other_business = Business.objects.create(name="Business Two")

        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            code=RoleCode.OWNER,
        )
        self.other_role = Role.objects.create(
            business=self.other_business,
            name="Owner",
            code=RoleCode.OWNER,
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

        self.client.force_authenticate(self.user)

    def detail_endpoint(self, supplier_id: int) -> str:
        return f"{self.endpoint}{supplier_id}/"

    def create_supplier(
        self,
        *,
        business: Business | None = None,
        name: str = "Test Supplier",
        is_active: bool = True,
    ) -> DjangoSupplier:
        return DjangoSupplier.objects.create(
            business=business or self.business,
            name=name,
            is_active=is_active,
        )

    def test_authenticated_user_can_create_supplier(self) -> None:
        response = self.client.post(
            self.endpoint,
            {
                "name": "Created Supplier",
                "phone": "123",
                "email": "supplier@example.com",
                "address": "Address",
                "tax_number": "TAX-1",
                "notes": "Notes",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Created Supplier")

    def test_business_id_cannot_be_supplied_by_client_to_create(self) -> None:
        response = self.client.post(
            self.endpoint,
            {
                "business_id": self.other_business.id,
                "name": "Spoofed Supplier",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["business_id"], self.business.id)

    def test_created_supplier_belongs_to_current_business(self) -> None:
        response = self.client.post(
            self.endpoint,
            {"name": "Current Business Supplier"},
            format="json",
        )

        supplier = DjangoSupplier.objects.get(id=response.data["id"])

        self.assertEqual(supplier.business_id, self.business.id)

    def test_user_can_list_only_suppliers_belonging_to_current_business(self) -> None:
        supplier = self.create_supplier(name="Visible Supplier")
        self.create_supplier(
            business=self.other_business,
            name="Hidden Supplier",
        )

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [supplier.id])

    def test_search_is_scoped_to_current_business(self) -> None:
        supplier = self.create_supplier(name="Scoped Match")
        self.create_supplier(
            business=self.other_business,
            name="Scoped Match",
        )

        response = self.client.get(
            self.endpoint,
            {"search": "Scoped"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [supplier.id])

    def test_user_can_retrieve_supplier_belonging_to_current_business(self) -> None:
        supplier = self.create_supplier(name="Visible Supplier")

        response = self.client.get(self.detail_endpoint(supplier.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], supplier.id)

    def test_user_cannot_retrieve_supplier_belonging_to_another_business(self) -> None:
        supplier = self.create_supplier(
            business=self.other_business,
            name="Hidden Supplier",
        )

        response = self.client.get(self.detail_endpoint(supplier.id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_can_update_supplier_belonging_to_current_business(self) -> None:
        supplier = self.create_supplier(name="Original Supplier")

        response = self.client.put(
            self.detail_endpoint(supplier.id),
            {
                "name": "Updated Supplier",
                "phone": "123",
                "email": "updated@example.com",
                "address": "Updated Address",
                "tax_number": "TAX-2",
                "notes": "Updated Notes",
                "is_active": False,
            },
            format="json",
        )

        supplier.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(supplier.name, "Updated Supplier")
        self.assertFalse(supplier.is_active)

    def test_user_cannot_update_supplier_belonging_to_another_business(self) -> None:
        supplier = self.create_supplier(
            business=self.other_business,
            name="Hidden Supplier",
        )

        response = self.client.put(
            self.detail_endpoint(supplier.id),
            {
                "name": "Updated Supplier",
                "is_active": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_client_cannot_move_supplier_to_another_business(self) -> None:
        supplier = self.create_supplier(name="Original Supplier")

        response = self.client.put(
            self.detail_endpoint(supplier.id),
            {
                "business_id": self.other_business.id,
                "name": "Updated Supplier",
                "is_active": True,
            },
            format="json",
        )

        supplier.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["business_id"], self.business.id)
        self.assertEqual(supplier.business_id, self.business.id)

    def test_duplicate_supplier_name_is_rejected_only_within_same_business(self) -> None:
        self.create_supplier(name="Duplicate Supplier")

        response = self.client.post(
            self.endpoint,
            {"name": "Duplicate Supplier"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_supplier_name_is_allowed_in_another_business(self) -> None:
        self.create_supplier(name="Shared Supplier")
        self.client.force_authenticate(self.other_user)

        response = self.client.post(
            self.endpoint,
            {"name": "Shared Supplier"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["business_id"], self.other_business.id)

    def test_is_active_filtering_works(self) -> None:
        active_supplier = self.create_supplier(
            name="Active Supplier",
            is_active=True,
        )
        self.create_supplier(
            name="Inactive Supplier",
            is_active=False,
        )

        response = self.client.get(
            self.endpoint,
            {"is_active": "true"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [item["id"] for item in response.data],
            [active_supplier.id],
        )

    def test_unauthenticated_access_is_rejected(self) -> None:
        self.client.force_authenticate(user=None)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DjangoPurchaseOrderRepositoryTests(TestCase):
    def setUp(self) -> None:
        self.business_1 = Business.objects.create(name="Business One")
        self.business_2 = Business.objects.create(name="Business Two")
        self.user_1 = User.objects.create_user(
            email="po-requester@example.com",
            password="password",
            name="PO Requester",
            number="4001",
        )
        self.user_2 = User.objects.create_user(
            email="other-po-requester@example.com",
            password="password",
            name="Other PO Requester",
            number="4002",
        )
        self.supplier_1 = DjangoSupplier.objects.create(
            business=self.business_1,
            name="Supplier One",
        )
        self.supplier_2 = DjangoSupplier.objects.create(
            business=self.business_2,
            name="Supplier Two",
        )
        self.ingredient_1 = Ingredient.objects.create(
            business=self.business_1,
            name="Ingredient One",
            unit=Ingredient.Unit.KG,
        )
        self.ingredient_2 = Ingredient.objects.create(
            business=self.business_1,
            name="Ingredient Two",
            unit=Ingredient.Unit.KG,
        )
        self.other_ingredient = Ingredient.objects.create(
            business=self.business_2,
            name="Other Ingredient",
            unit=Ingredient.Unit.KG,
        )
        self.repository = DjangoPurchaseOrderRepository()

    def create_order(
        self,
        *,
        business_id: int | None = None,
        supplier_id: int | None = None,
        requisition_id: int | None = None,
        order_date: date = date(2026, 9, 7),
        status: PurchaseOrderStatus = PurchaseOrderStatus.DRAFT,
        items: list[PurchaseOrderItem] | None = None,
    ) -> PurchaseOrder:
        return self.repository.save(
            PurchaseOrder(
                id=None,
                business_id=business_id or self.business_1.id,
                supplier_id=supplier_id or self.supplier_1.id,
                requisition_id=requisition_id,
                order_date=order_date,
                status=status,
                items=items
                or [
                    PurchaseOrderItem(
                        self.ingredient_1.id,
                        Decimal("2"),
                        Decimal("3"),
                    )
                ],
            )
        )

    def test_create_and_get_hydrates_order_and_items(self) -> None:
        order = self.create_order(
            items=[
                PurchaseOrderItem(self.ingredient_1.id, Decimal("2"), Decimal("3")),
                PurchaseOrderItem(self.ingredient_2.id, Decimal("1"), Decimal("4")),
            ]
        )

        result = self.repository.get_by_id_for_business(
            order.id,
            self.business_1.id,
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.business_id, self.business_1.id)
        self.assertEqual(len(result.items), 2)
        self.assertEqual(result.total_amount(), Decimal("10"))

    def test_get_from_other_business_returns_none(self) -> None:
        order = self.create_order()

        self.assertIsNone(
            self.repository.get_by_id_for_business(order.id, self.business_2.id)
        )

    def test_list_is_tenant_scoped_and_supports_filters(self) -> None:
        requisition = DjangoPurchaseRequisition.objects.create(
            business=self.business_1,
            requested_by=self.user_1,
            status=DjangoPurchaseRequisition.Status.APPROVED,
        )
        draft = self.create_order(requisition_id=requisition.id)
        sent = self.create_order(
            supplier_id=self.supplier_1.id,
            order_date=date(2026, 9, 8),
            status=PurchaseOrderStatus.SENT,
        )
        other = self.create_order(
            business_id=self.business_2.id,
            supplier_id=self.supplier_2.id,
            items=[PurchaseOrderItem(self.other_ingredient.id, Decimal("1"), Decimal("1"))],
        )

        self.assertEqual(
            [order.id for order in self.repository.list(self.business_1.id)],
            [draft.id, sent.id],
        )
        self.assertEqual(
            [order.id for order in self.repository.list(
                self.business_1.id,
                status=PurchaseOrderStatus.SENT,
            )],
            [sent.id],
        )
        self.assertEqual(
            [order.id for order in self.repository.list(
                self.business_1.id,
                supplier_id=self.supplier_1.id,
            )],
            [draft.id, sent.id],
        )
        self.assertEqual(
            [order.id for order in self.repository.list(
                self.business_1.id,
                requisition_id=requisition.id,
            )],
            [draft.id],
        )
        self.assertEqual(
            [order.id for order in self.repository.list(
                self.business_1.id,
                order_date_from=date(2026, 9, 8),
                order_date_to=date(2026, 9, 8),
            )],
            [sent.id],
        )
        self.assertNotIn(other.id, [order.id for order in self.repository.list(self.business_1.id)])

    def test_exists_by_requisition_is_tenant_scoped(self) -> None:
        requisition = DjangoPurchaseRequisition.objects.create(
            business=self.business_1,
            requested_by=self.user_1,
            status=DjangoPurchaseRequisition.Status.APPROVED,
        )
        order = self.create_order(requisition_id=requisition.id)

        self.assertTrue(
            self.repository.exists_by_requisition(
                self.business_1.id,
                requisition.id,
            )
        )
        self.assertFalse(
            self.repository.exists_by_requisition(
                self.business_2.id,
                requisition.id,
            )
        )
        self.assertEqual(order.requisition_id, requisition.id)

    def test_update_synchronizes_stale_new_and_duplicate_items(self) -> None:
        order = self.create_order()
        stale_item_id = DjangoPurchaseOrderItem.objects.get(
            purchase_order_id=order.id,
        ).id
        order.items = [
            PurchaseOrderItem(self.ingredient_2.id, Decimal("4"), Decimal("5")),
            PurchaseOrderItem(self.ingredient_2.id, Decimal("6"), Decimal("7")),
        ]

        result = self.repository.save(order)
        item_models = list(
            DjangoPurchaseOrderItem.objects.filter(
                purchase_order_id=order.id,
            ).order_by("id")
        )

        self.assertEqual(len(item_models), 2)
        self.assertFalse(
            DjangoPurchaseOrderItem.objects.filter(id=stale_item_id).exists()
        )
        self.assertEqual(
            [(item.ingredient_id, item.quantity, item.unit_price) for item in result.items],
            [
                (self.ingredient_2.id, Decimal("4"), Decimal("5")),
                (self.ingredient_2.id, Decimal("6"), Decimal("7")),
            ],
        )

    def test_received_purchase_order_terms_and_lines_are_immutable(self) -> None:
        order = self.create_order(status=PurchaseOrderStatus.RECEIVED)
        order.items[0].quantity = Decimal("999")
        with self.assertRaisesRegex(ValueError, "cannot be changed after it is sent"):
            self.repository.save(order)

    def test_cancelled_purchase_order_cannot_be_reopened(self) -> None:
        order = self.create_order(status=PurchaseOrderStatus.CANCELLED)
        order.status = PurchaseOrderStatus.DRAFT
        with self.assertRaisesRegex(ValueError, "transition is not allowed"):
            self.repository.save(order)

    def test_cross_business_supplier_is_rejected_without_persisting(self) -> None:
        with self.assertRaises(ValueError):
            self.create_order(supplier_id=self.supplier_2.id)

        self.assertEqual(DjangoPurchaseOrder.objects.count(), 0)

    def test_cross_business_requisition_is_rejected(self) -> None:
        requisition = DjangoPurchaseRequisition.objects.create(
            business=self.business_2,
            requested_by=self.user_2,
            status=DjangoPurchaseRequisition.Status.APPROVED,
        )

        with self.assertRaises(ValueError):
            self.create_order(requisition_id=requisition.id)

    def test_cross_business_ingredient_is_rejected_without_partial_write(self) -> None:
        with self.assertRaises(ValueError):
            self.create_order(
                items=[
                    PurchaseOrderItem(self.ingredient_1.id, Decimal("1"), Decimal("1")),
                    PurchaseOrderItem(self.other_ingredient.id, Decimal("1"), Decimal("1")),
                ]
            )

        self.assertEqual(DjangoPurchaseOrder.objects.count(), 0)

    def test_existing_order_from_other_business_cannot_be_mutated(self) -> None:
        order = self.create_order()
        malicious = PurchaseOrder(
            id=order.id,
            business_id=self.business_2.id,
            supplier_id=self.supplier_2.id,
            order_date=order.order_date,
            items=[
                PurchaseOrderItem(self.other_ingredient.id, Decimal("9"), Decimal("9")),
            ],
        )

        with self.assertRaises(ValueError):
            self.repository.save(malicious)

        persisted = DjangoPurchaseOrder.objects.get(id=order.id)
        self.assertEqual(persisted.business_id, self.business_1.id)
        self.assertEqual(persisted.items.count(), 1)


class PurchaseOrderAPITests(APITestCase):
    endpoint = "/api/purchase/purchase-orders/"

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="purchase-order-owner@example.com",
            password="password",
            name="Purchase Order Owner",
            number="5001",
        )
        self.other_user = User.objects.create_user(
            email="other-purchase-order-owner@example.com",
            password="password",
            name="Other Purchase Order Owner",
            number="5002",
        )
        self.business = Business.objects.create(name="PO Business")
        self.other_business = Business.objects.create(name="Other PO Business")
        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            code=RoleCode.OWNER,
        )
        self.other_role = Role.objects.create(
            business=self.other_business,
            name="Owner",
            code=RoleCode.OWNER,
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
        self.supplier = DjangoSupplier.objects.create(
            business=self.business,
            name="PO Supplier",
        )
        self.other_supplier = DjangoSupplier.objects.create(
            business=self.other_business,
            name="Other Supplier",
        )
        self.ingredient = Ingredient.objects.create(
            business=self.business,
            name="PO Ingredient",
            unit=Ingredient.Unit.KG,
        )
        self.other_ingredient = Ingredient.objects.create(
            business=self.other_business,
            name="Other PO Ingredient",
            unit=Ingredient.Unit.KG,
        )
        self.client.force_authenticate(self.user)

    def detail_endpoint(self, purchase_order_id: int) -> str:
        return f"{self.endpoint}{purchase_order_id}/"

    def action_endpoint(self, purchase_order_id: int, action: str) -> str:
        return f"{self.detail_endpoint(purchase_order_id)}{action}/"

    def create_payload(self, **overrides: object) -> dict:
        payload = {
            "supplier_id": self.supplier.id,
            "order_date": "2026-09-07",
            "expected_date": "2026-09-14",
            "discount": "1.00",
            "tax": "2.00",
            "items": [
                {
                    "ingredient_id": self.ingredient.id,
                    "quantity": "2.000",
                    "unit_price": "3.00",
                }
            ],
        }
        payload.update(overrides)
        return payload

    def create_order(self, **overrides: object):
        return self.client.post(
            self.endpoint,
            self.create_payload(**overrides),
            format="json",
        )

    def create_other_business_order(self) -> DjangoPurchaseOrder:
        return DjangoPurchaseOrder.objects.create(
            business=self.other_business,
            supplier=self.other_supplier,
            order_date=date(2026, 9, 7),
            status=DjangoPurchaseOrder.Status.DRAFT,
        )

    def test_create_purchase_order(self) -> None:
        response = self.create_order()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["business_id"], self.business.id)
        self.assertEqual(response.data["status"], "draft")

    def test_client_business_id_and_status_cannot_override_tenant_or_lifecycle(self) -> None:
        response = self.create_order(
            business_id=self.other_business.id,
            status="received",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["business_id"], self.business.id)
        self.assertEqual(response.data["status"], "draft")

    def test_list_purchase_orders(self) -> None:
        created = self.create_order()

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [created.data["id"]])

    def test_get_purchase_order(self) -> None:
        created = self.create_order()

        response = self.client.get(self.detail_endpoint(created.data["id"]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], created.data["id"])

    def test_update_draft_purchase_order(self) -> None:
        created = self.create_order()
        response = self.client.put(
            self.detail_endpoint(created.data["id"]),
            self.create_payload(
                items=[
                    {
                        "ingredient_id": self.ingredient.id,
                        "quantity": "4.000",
                        "unit_price": "5.00",
                    }
                ],
                discount="2.00",
                tax="3.00",
            ),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["items"][0]["quantity"], "4.000")

    def test_send_purchase_order(self) -> None:
        created = self.create_order()

        response = self.client.post(
            self.action_endpoint(created.data["id"], "send"),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "sent")

    def test_cancel_purchase_order(self) -> None:
        created = self.create_order()

        response = self.client.post(
            self.action_endpoint(created.data["id"], "cancel"),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "cancelled")

    def test_invalid_send_transition_returns_bad_request(self) -> None:
        created = self.create_order()
        self.client.post(self.action_endpoint(created.data["id"], "send"), {})

        response = self.client.post(
            self.action_endpoint(created.data["id"], "send"),
            {},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_cancel_transition_returns_bad_request(self) -> None:
        order = DjangoPurchaseOrder.objects.create(
            business=self.business,
            supplier=self.supplier,
            order_date=date(2026, 9, 7),
            status=DjangoPurchaseOrder.Status.RECEIVED,
        )

        response = self.client.post(
            self.action_endpoint(order.id, "cancel"),
            {},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cross_business_detail_returns_not_found(self) -> None:
        order = self.create_other_business_order()

        response = self.client.get(self.detail_endpoint(order.id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cross_business_update_returns_not_found(self) -> None:
        order = self.create_other_business_order()

        response = self.client.put(
            self.detail_endpoint(order.id),
            self.create_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cross_business_send_returns_not_found(self) -> None:
        order = self.create_other_business_order()

        response = self.client.post(self.action_endpoint(order.id, "send"), {})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cross_business_cancel_returns_not_found(self) -> None:
        order = self.create_other_business_order()

        response = self.client.post(self.action_endpoint(order.id, "cancel"), {})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_create_is_rejected(self) -> None:
        self.client.force_authenticate(user=None)

        response = self.client.post(self.endpoint, self.create_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_list_is_rejected(self) -> None:
        self.client.force_authenticate(user=None)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_supplier_ownership_is_rejected(self) -> None:
        response = self.create_order(supplier_id=self.other_supplier.id)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_requisition_ownership_is_rejected(self) -> None:
        requisition = DjangoPurchaseRequisition.objects.create(
            business=self.other_business,
            requested_by=self.other_user,
            status=DjangoPurchaseRequisition.Status.APPROVED,
        )

        response = self.create_order(requisition_id=requisition.id)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_filters_are_forwarded(self) -> None:
        requisition = DjangoPurchaseRequisition.objects.create(
            business=self.business,
            requested_by=self.user,
            status=DjangoPurchaseRequisition.Status.APPROVED,
        )
        order = DjangoPurchaseOrder.objects.create(
            business=self.business,
            supplier=self.supplier,
            requisition=requisition,
            order_date=date(2026, 9, 7),
            status=DjangoPurchaseOrder.Status.SENT,
        )

        for query in (
            {"status": "sent"},
            {"supplier_id": str(self.supplier.id)},
            {"requisition_id": str(requisition.id)},
            {"order_date_from": "2026-09-07", "order_date_to": "2026-09-07"},
        ):
            response = self.client.get(self.endpoint, query)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual([item["id"] for item in response.data], [order.id])


class RequisitionAPITests(APITestCase):
    endpoint = "/api/purchase/requisitions/"

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="requester@example.com",
            password="password",
            name="Requester",
            number="3001",
        )
        self.other_user = User.objects.create_user(
            email="other-requester@example.com",
            password="password",
            name="Other Requester",
            number="3002",
        )
        self.business = Business.objects.create(name="Business One")
        self.other_business = Business.objects.create(name="Business Two")
        self.role = Role.objects.create(
            business=self.business,
            name="Owner",
            code=RoleCode.OWNER,
        )
        self.other_role = Role.objects.create(
            business=self.other_business,
            name="Owner",
            code=RoleCode.OWNER,
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
        self.ingredient = Ingredient.objects.create(
            business=self.business,
            name="Flour",
            unit=Ingredient.Unit.KG,
        )
        self.other_ingredient = Ingredient.objects.create(
            business=self.other_business,
            name="Other Flour",
            unit=Ingredient.Unit.KG,
        )
        self.client.force_authenticate(self.user)

    def detail_endpoint(self, requisition_id: int) -> str:
        return f"{self.endpoint}{requisition_id}/"

    def action_endpoint(self, requisition_id: int, action: str) -> str:
        return f"{self.detail_endpoint(requisition_id)}{action}/"

    def create_requisition(self, **data: object):
        payload = {
            "reason": "Stock replenishment",
            "items": [
                {
                    "ingredient_id": self.ingredient.id,
                    "quantity": "2.000",
                    "note": "Needed",
                }
            ],
        }
        payload.update(data)
        return self.client.post(self.endpoint, payload, format="json")

    def submit_requisition(self, requisition_id: int) -> None:
        response = self.client.post(
            self.action_endpoint(requisition_id, "submit"),
            {},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_requisition_uses_current_business_and_user(self) -> None:
        response = self.create_requisition(
            business_id=self.other_business.id,
            requested_by_id=self.other_user.id,
            status="approved",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["business_id"], self.business.id)
        self.assertEqual(response.data["requested_by_id"], self.user.id)
        self.assertEqual(response.data["status"], "draft")
        self.assertEqual(response.data["items"][0]["ingredient_id"], self.ingredient.id)

    def test_list_requisitions(self) -> None:
        created = self.create_requisition()
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [created.data["id"]])

    def test_get_requisition(self) -> None:
        created = self.create_requisition()

        response = self.client.get(self.detail_endpoint(created.data["id"]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], created.data["id"])

    def test_cross_business_get_returns_not_found(self) -> None:
        requisition = DjangoPurchaseRequisition.objects.create(
            business=self.other_business,
            requested_by=self.other_user,
            reason="Other business",
        )

        response = self.client.get(self.detail_endpoint(requisition.id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_submit_requisition(self) -> None:
        created = self.create_requisition()

        response = self.client.post(
            self.action_endpoint(created.data["id"], "submit"),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "submitted")

    def test_approve_requisition(self) -> None:
        created = self.create_requisition()
        self.submit_requisition(created.data["id"])

        response = self.client.post(
            self.action_endpoint(created.data["id"], "approve"),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "approved")

    def test_reject_requisition(self) -> None:
        created = self.create_requisition()
        self.submit_requisition(created.data["id"])

        response = self.client.post(
            self.action_endpoint(created.data["id"], "reject"),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "rejected")

    def test_invalid_lifecycle_transition_returns_bad_request(self) -> None:
        created = self.create_requisition()

        response = self.client.post(
            self.action_endpoint(created.data["id"], "approve"),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_access_is_rejected(self) -> None:
        self.client.force_authenticate(user=None)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
