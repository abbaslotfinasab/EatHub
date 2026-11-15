from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Permission, Role, RolePermission, User
from core.enums import PermissionCode
from products.models import Order, OrderStatusHistory


class OrderStatusPermissionMatrixApiTests(APITestCase):
    endpoint_template = "/api/products/orders/{order_id}/status/"

    def setUp(self):
        self.business = Business.objects.create(
            name="Order Status Permission Business",
            inventory_enabled=False,
        )
        self.user = User.objects.create_user(
            email="order-status-permissions@example.test",
            password="test-password",
            name="Order Status Permission User",
            number="77901",
        )
        self.role = Role.objects.create(
            business=self.business,
            name="Custom Order Operator",
            code="CUSTOM_ORDER_OPERATOR",
        )
        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=self.role,
            is_active=True,
        )
        self._grant(PermissionCode.ORDERS_UPDATE)
        self._grant(PermissionCode.ORDERS_CANCEL)
        self.client.force_authenticate(self.user)
        self.client.defaults["HTTP_X_BUSINESS_ID"] = str(self.business.pk)

    def _grant(self, permission_code):
        permission, _ = Permission.objects.get_or_create(
            code=permission_code.value,
            defaults={"name": permission_code.label},
        )
        RolePermission.objects.get_or_create(role=self.role, permission=permission)

    def _revoke(self, permission_code):
        RolePermission.objects.filter(
            role=self.role,
            permission__code=permission_code.value,
        ).delete()

    def _create_order(self, current_status):
        return Order.objects.create(
            business=self.business,
            order_type=Order.OrderType.TAKEAWAY,
            status=current_status,
            payment_method=Order.PaymentMethod.CASH,
            payment_status=Order.PaymentStatus.PENDING,
            inventory_tracking_enabled=False,
        )

    def _patch_status(self, order, target_status):
        return self.client.patch(
            self.endpoint_template.format(order_id=order.pk),
            {"status": target_status},
            format="json",
        )

    def test_inventory_sensitive_transitions_require_inventory_fulfill_permission(self):
        cases = (
            (Order.Status.PENDING, Order.Status.CONFIRMED),
            (Order.Status.PREPARING, Order.Status.READY),
            (Order.Status.PENDING, Order.Status.FAILED),
            (Order.Status.PENDING, Order.Status.CANCELLED),
        )

        # CANCELLED has its separate permission, so this isolates the
        # inventory fulfillment requirement rather than failing earlier.
        self._revoke(PermissionCode.INVENTORY_ORDER_FULFILL)

        for current_status, target_status in cases:
            with self.subTest(current=current_status, target=target_status):
                order = self._create_order(current_status)
                response = self._patch_status(order, target_status)

                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
                order.refresh_from_db()
                self.assertEqual(order.status, current_status)
                self.assertFalse(
                    OrderStatusHistory.objects.filter(
                        business=self.business,
                        order_id_snapshot=order.pk,
                    ).exists()
                )

    def test_cancel_also_requires_orders_cancel_permission(self):
        self._revoke(PermissionCode.ORDERS_CANCEL)
        self._grant(PermissionCode.INVENTORY_ORDER_FULFILL)
        order = self._create_order(Order.Status.PENDING)

        response = self._patch_status(order, Order.Status.CANCELLED)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertFalse(
            OrderStatusHistory.objects.filter(order_id_snapshot=order.pk).exists()
        )

    def test_status_mutation_requires_orders_update_permission(self):
        self._revoke(PermissionCode.ORDERS_UPDATE)
        self._grant(PermissionCode.INVENTORY_ORDER_FULFILL)
        order = self._create_order(Order.Status.PENDING)

        response = self._patch_status(order, Order.Status.FAILED)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)

    def test_non_inventory_transitions_work_without_inventory_fulfill_permission(self):
        self._revoke(PermissionCode.INVENTORY_ORDER_FULFILL)
        order = self._create_order(Order.Status.CONFIRMED)

        preparing = self._patch_status(order, Order.Status.PREPARING)

        self.assertEqual(preparing.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PREPARING)

        completed = self._patch_status(order, Order.Status.COMPLETED)

        self.assertEqual(completed.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.COMPLETED)
        self.assertEqual(
            list(
                OrderStatusHistory.objects.filter(order_id_snapshot=order.pk)
                .order_by("created_at", "pk")
                .values_list("from_status", "to_status")
            ),
            [
                (Order.Status.CONFIRMED, Order.Status.PREPARING),
                (Order.Status.PREPARING, Order.Status.COMPLETED),
            ],
        )
