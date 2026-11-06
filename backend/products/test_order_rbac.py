from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Permission, Role, RolePermission, User
from accounts.services.rbac_initializer import RBACInitializer
from core.enums import PermissionCode
from products.models import Order


class OrderRBACApiTests(APITestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Order RBAC Business")
        self.user = User.objects.create_user(
            email="order-rbac@example.com",
            password="password",
            name="Order RBAC User",
            number="88001",
        )
        self.role = Role.objects.create(
            business=self.business,
            name="Custom Order Role",
            code="CUSTOM_ORDER_ROLE",
        )
        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=self.role,
            is_active=True,
        )
        for permission in PermissionCode:
            Permission.objects.get_or_create(
                code=permission.value,
                defaults={"name": permission.label},
            )
        self.client.force_authenticate(self.user)
        self.order = self.create_order()

    def create_order(self):
        return Order.objects.create(
            business=self.business,
            order_type=Order.OrderType.TAKEAWAY,
            status=Order.Status.PENDING,
            payment_method=Order.PaymentMethod.CASH,
            payment_status=Order.PaymentStatus.PENDING,
            subtotal=Decimal("10.00"),
            total_amount=Decimal("10.00"),
        )

    def grant(self, *permission_codes):
        for code in permission_codes:
            permission = Permission.objects.get(code=code)
            RolePermission.objects.get_or_create(
                role=self.role,
                permission=permission,
            )

    def test_order_read_and_create_endpoints_require_explicit_permissions(self):
        list_response = self.client.get("/api/products/orders/list/")
        detail_response = self.client.get(f"/api/products/orders/{self.order.pk}/")
        create_response = self.client.post("/api/products/orders/", {}, format="json")

        self.assertEqual(list_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(detail_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_orders_view_grants_read_but_not_create_or_mutation(self):
        self.grant(PermissionCode.ORDERS_VIEW)

        list_response = self.client.get("/api/products/orders/list/")
        detail_response = self.client.get(f"/api/products/orders/{self.order.pk}/")
        create_response = self.client.post("/api/products/orders/", {}, format="json")
        update_response = self.client.patch(
            f"/api/products/orders/{self.order.pk}/update/",
            {"notes": "Unauthorized"},
            format="json",
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(update_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_order_update_without_delete_permission_cannot_delete(self):
        self.grant(PermissionCode.ORDERS_UPDATE)

        response = self.client.delete(
            f"/api/products/orders/{self.order.pk}/delete/"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Order.objects.filter(pk=self.order.pk).exists())

    def test_order_update_without_cancel_permission_cannot_cancel(self):
        self.grant(
            PermissionCode.ORDERS_UPDATE,
            PermissionCode.INVENTORY_ORDER_FULFILL,
        )

        response = self.client.patch(
            f"/api/products/orders/{self.order.pk}/status/",
            {"status": Order.Status.CANCELLED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)

    def test_inventory_consumption_read_requires_order_view_and_inventory_permission(self):
        self.grant(
            PermissionCode.ORDERS_UPDATE,
            PermissionCode.INVENTORY_ORDER_FULFILL,
        )

        response = self.client.get(
            f"/api/products/orders/{self.order.pk}/consumption/"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_order_delete_permission_allows_only_service_eligible_pending_order(self):
        self.grant(PermissionCode.ORDERS_DELETE)

        response = self.client.delete(
            f"/api/products/orders/{self.order.pk}/delete/"
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Order.objects.filter(pk=self.order.pk).exists())

    def test_manager_can_cancel_but_cannot_delete_orders(self):
        RBACInitializer.initialize(self.business)
        manager = Role.objects.get(business=self.business, code="MANAGER")
        manager_user = User.objects.create_user(
            email="order-rbac-manager@example.com",
            password="password",
            name="Order RBAC Manager",
            number="88002",
        )
        Membership.objects.create(
            user=manager_user,
            business=self.business,
            role=manager,
            is_active=True,
        )
        self.client.force_authenticate(manager_user)

        cancel_response = self.client.patch(
            f"/api/products/orders/{self.order.pk}/status/",
            {"status": Order.Status.CANCELLED},
            format="json",
        )
        delete_response = self.client.delete(
            f"/api/products/orders/{self.order.pk}/delete/"
        )

        self.assertEqual(cancel_response.status_code, status.HTTP_200_OK)
        self.assertEqual(delete_response.status_code, status.HTTP_403_FORBIDDEN)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CANCELLED)

    def test_default_roles_receive_only_intended_order_lifecycle_permissions(self):
        RBACInitializer.initialize(self.business)
        manager = Role.objects.get(business=self.business, code="MANAGER")
        owner = Role.objects.get(business=self.business, code="OWNER")

        manager_permissions = set(
            manager.role_permissions.values_list("permission__code", flat=True)
        )
        owner_permissions = set(
            owner.role_permissions.values_list("permission__code", flat=True)
        )

        self.assertIn(PermissionCode.ORDERS_CANCEL, manager_permissions)
        self.assertNotIn(PermissionCode.ORDERS_DELETE, manager_permissions)
        self.assertIn(PermissionCode.ORDERS_DELETE, owner_permissions)
        self.assertIn(PermissionCode.ORDERS_CANCEL, owner_permissions)
