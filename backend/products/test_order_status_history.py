from decimal import Decimal
from unittest import skipUnless
from unittest.mock import patch

from django.db import DatabaseError, connection, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Permission, Role, RolePermission, User
from core.enums import PermissionCode
from products.models import Menu, MenuItem, Order, OrderStatusHistory
from products.services.order_service import OrderService


class OrderStatusHistoryServiceTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Order History Business")
        self.actor = User.objects.create_user(
            email="order-history@example.test",
            password="test-password",
            name="Order History Actor",
            number="77101",
        )
        self.order = Order.objects.create(
            business=self.business,
            order_type=Order.OrderType.TAKEAWAY,
            status=Order.Status.PENDING,
            payment_method=Order.PaymentMethod.CASH,
        )

    @patch("products.services.order_service.OrderInventoryService.release_remaining")
    def test_status_transition_records_actor_and_previous_and_next_status(self, release):
        updated = OrderService.update_status(
            business=self.business,
            order_id=self.order.pk,
            status=Order.Status.CANCELLED,
            user=self.actor,
        )

        self.assertEqual(updated.status, Order.Status.CANCELLED)
        entry = OrderStatusHistory.objects.get(order_id_snapshot=self.order.pk)
        self.assertEqual(entry.business_id, self.business.pk)
        self.assertEqual(entry.from_status, Order.Status.PENDING)
        self.assertEqual(entry.to_status, Order.Status.CANCELLED)
        self.assertEqual(entry.actor_id, self.actor.pk)
        release.assert_called_once()

    def test_business_deletion_is_protected_while_audit_history_exists(self):
        history = OrderStatusHistory.objects.create(
            business=self.business,
            order_id_snapshot=self.order.pk,
            from_status=None,
            to_status=Order.Status.PENDING,
            actor=self.actor,
        )

        with self.assertRaises(ProtectedError):
            self.business.delete()

        self.assertTrue(OrderStatusHistory.objects.filter(pk=history.pk).exists())
        self.assertTrue(Business.objects.filter(pk=self.business.pk).exists())

    @skipUnless(connection.vendor == "postgresql", "PostgreSQL trigger enforcement")
    def test_bulk_update_cannot_mutate_status_history(self):
        history = OrderStatusHistory.objects.create(
            business=self.business,
            order_id_snapshot=self.order.pk,
            from_status=None,
            to_status=Order.Status.PENDING,
            actor=self.actor,
        )

        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                OrderStatusHistory.objects.filter(pk=history.pk).update(
                    to_status=Order.Status.COMPLETED
                )

        history.refresh_from_db()
        self.assertEqual(history.to_status, Order.Status.PENDING)

    @skipUnless(connection.vendor == "postgresql", "PostgreSQL trigger enforcement")
    def test_bulk_delete_cannot_remove_status_history(self):
        history = OrderStatusHistory.objects.create(
            business=self.business,
            order_id_snapshot=self.order.pk,
            from_status=None,
            to_status=Order.Status.PENDING,
            actor=self.actor,
        )

        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                OrderStatusHistory.objects.filter(pk=history.pk).delete()

        self.assertTrue(OrderStatusHistory.objects.filter(pk=history.pk).exists())

    def test_actor_deletion_is_protected_to_preserve_audit_attribution(self):
        history = OrderStatusHistory.objects.create(
            business=self.business,
            order_id_snapshot=self.order.pk,
            from_status=None,
            to_status=Order.Status.PENDING,
            actor=self.actor,
        )

        with self.assertRaises(ProtectedError):
            self.actor.delete()

        history.refresh_from_db()
        self.assertEqual(history.actor_id, self.actor.pk)

    def test_history_survives_deletion_of_a_pending_order(self):
        history = OrderStatusHistory.objects.create(
            business=self.business,
            order_id_snapshot=self.order.pk,
            from_status=None,
            to_status=Order.Status.PENDING,
            actor=self.actor,
        )
        order_id = self.order.pk

        self.order.delete()

        history.refresh_from_db()
        self.assertEqual(history.order_id_snapshot, order_id)
        self.assertTrue(OrderStatusHistory.objects.filter(order_id_snapshot=order_id).exists())

    def test_repeating_current_status_does_not_create_a_transition_event(self):
        OrderService.update_status(
            business=self.business,
            order_id=self.order.pk,
            status=Order.Status.PENDING,
            user=self.actor,
        )

        self.assertFalse(OrderStatusHistory.objects.filter(order_id_snapshot=self.order.pk).exists())

    @patch(
        "products.services.order_service.OrderInventoryService.release_remaining",
        side_effect=RuntimeError("inventory release failed"),
    )
    def test_failed_inventory_side_effect_rolls_back_status_and_history(self, release):
        with self.assertRaises(RuntimeError):
            OrderService.update_status(
                business=self.business,
                order_id=self.order.pk,
                status=Order.Status.CANCELLED,
                user=self.actor,
            )

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)
        self.assertFalse(OrderStatusHistory.objects.filter(order_id_snapshot=self.order.pk).exists())

    def test_order_creation_records_initial_pending_state(self):
        menu = Menu.objects.create(
            business=self.business,
            name="History Menu",
            category="Test",
        )
        menu_item = MenuItem.objects.create(
            business=self.business,
            menu=menu,
            name="History Item",
            price=Decimal("12.50"),
        )

        order = OrderService.create_order(
            business=self.business,
            user=self.actor,
            validated_data={
                "order_type": Order.OrderType.TAKEAWAY,
                "items": [{"menu_item_id": menu_item.pk, "quantity": 1}],
                "discount": Decimal("0"),
                "tax": Decimal("0"),
            },
        )

        entry = OrderStatusHistory.objects.get(order=order)
        self.assertIsNone(entry.from_status)
        self.assertEqual(entry.to_status, Order.Status.PENDING)
        self.assertEqual(entry.actor_id, self.actor.pk)


class OrderStatusHistoryApiTests(APITestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Order History API Business")
        self.user = User.objects.create_user(
            email="order-history-api@example.test",
            password="test-password",
            name="Order History API User",
            number="77102",
        )
        self.role = Role.objects.create(
            business=self.business,
            name="Order Reader",
            code="ORDER_HISTORY_READER",
        )
        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=self.role,
            is_active=True,
        )
        permission, _ = Permission.objects.get_or_create(
            code=PermissionCode.ORDERS_VIEW.value,
            defaults={"name": PermissionCode.ORDERS_VIEW.label},
        )
        self.view_permission = permission
        self.order = Order.objects.create(
            business=self.business,
            order_type=Order.OrderType.TAKEAWAY,
            status=Order.Status.PREPARING,
        )
        self.client.force_authenticate(self.user)
        self.client.defaults["HTTP_X_BUSINESS_ID"] = str(self.business.pk)

    def grant_order_view(self):
        RolePermission.objects.get_or_create(
            role=self.role,
            permission=self.view_permission,
        )

    def test_history_endpoint_returns_chronological_status_events(self):
        self.grant_order_view()
        OrderStatusHistory.objects.create(
            business=self.business,
            order_id_snapshot=self.order.pk,
            from_status=None,
            to_status=Order.Status.PENDING,
            actor=self.user,
        )
        OrderStatusHistory.objects.create(
            business=self.business,
            order_id_snapshot=self.order.pk,
            from_status=Order.Status.PENDING,
            to_status=Order.Status.CONFIRMED,
            actor=self.user,
        )

        response = self.client.get(
            f"/api/products/orders/{self.order.pk}/history/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["order_id"], self.order.pk)
        self.assertEqual(
            [entry["to_status"] for entry in response.data["history"]],
            [Order.Status.PENDING, Order.Status.CONFIRMED],
        )
        self.assertEqual(
            response.data["history"][1]["actor"],
            {"id": self.user.pk, "name": self.user.name},
        )

    def test_history_endpoint_requires_orders_view_permission(self):
        response = self.client.get(
            f"/api/products/orders/{self.order.pk}/history/"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_history_endpoint_does_not_disclose_foreign_business_orders(self):
        self.grant_order_view()
        foreign_business = Business.objects.create(name="Foreign Order History Business")
        foreign_order = Order.objects.create(
            business=foreign_business,
            order_type=Order.OrderType.TAKEAWAY,
        )

        response = self.client.get(
            f"/api/products/orders/{foreign_order.pk}/history/"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
