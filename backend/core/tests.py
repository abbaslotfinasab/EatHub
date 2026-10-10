from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.db import DatabaseError
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Role, User
from core.models import ActivityLog
from products.models import Customer, Menu, MenuItem, Order, OrderItem
from products.services.order_service import OrderService


class DashboardRecentOrdersPaginationTests(APITestCase):
    endpoint = "/api/core/dashboard/"

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="dashboard-pagination@example.com",
            password="password",
            name="Dashboard Pagination User",
            number="8001",
        )
        self.other_user = User.objects.create_user(
            email="other-dashboard-pagination@example.com",
            password="password",
            name="Other Dashboard Pagination User",
            number="8002",
        )
        self.business = Business.objects.create(name="Dashboard Business")
        self.other_business = Business.objects.create(
            name="Other Dashboard Business",
        )
        role = Role.objects.create(
            business=self.business,
            name="Owner",
            code="OWNER",
        )
        other_role = Role.objects.create(
            business=self.other_business,
            name="Owner",
            code="OWNER",
        )
        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=role,
            is_active=True,
        )
        Membership.objects.create(
            user=self.other_user,
            business=self.other_business,
            role=other_role,
            is_active=True,
        )
        self.client.force_authenticate(self.user)

    def create_order(self, business=None, created_at=None, **overrides):
        order = Order.objects.create(
            business=business or self.business,
            order_type=Order.OrderType.DINE_IN,
            status=Order.Status.PENDING,
            payment_method=Order.PaymentMethod.CASH,
            payment_status=Order.PaymentStatus.PENDING,
            total_amount=10,
            **overrides,
        )
        if created_at is not None:
            Order.objects.filter(id=order.id).update(
                created_at=created_at,
            )
            order.refresh_from_db()
        return order

    def test_default_dashboard_pagination_and_response_shape(self):
        for _ in range(12):
            self.create_order()

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recent_orders = response.data["recent_orders"]
        self.assertEqual(recent_orders["count"], 12)
        self.assertEqual(len(recent_orders["results"]), 10)
        self.assertIsNone(recent_orders["previous"])
        self.assertIsNotNone(recent_orders["next"])
        self.assertIn("stats", response.data)
        self.assertIn("sales_chart", response.data)
        self.assertIn("inventory_alerts", response.data)
        self.assertIn("top_products", response.data)
        self.assertIn("activities", response.data)

    def test_custom_page_and_page_size(self):
        for _ in range(15):
            self.create_order()

        response = self.client.get(
            self.endpoint,
            {"page": 2, "page_size": 5},
        )

        recent_orders = response.data["recent_orders"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(recent_orders["count"], 15)
        self.assertEqual(len(recent_orders["results"]), 5)
        self.assertIsNotNone(recent_orders["previous"])
        self.assertIsNotNone(recent_orders["next"])

    def test_page_size_is_capped(self):
        for _ in range(60):
            self.create_order()

        response = self.client.get(
            self.endpoint,
            {"page_size": 1000},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data["recent_orders"]["results"]),
            50,
        )

    def test_recent_orders_are_tenant_and_today_scoped(self):
        self.create_order()
        self.create_order(business=self.other_business)
        self.create_order(
            created_at=timezone.now() - timedelta(days=1),
        )

        response = self.client.get(self.endpoint)

        recent_orders = response.data["recent_orders"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(recent_orders["count"], 1)
        self.assertEqual(len(recent_orders["results"]), 1)

    def test_top_products_use_api_names_and_group_stable_item_snapshots(self):
        menu = Menu.objects.create(
            business=self.business,
            name="Lunch",
            category="Food",
        )
        menu_item = MenuItem.objects.create(
            business=self.business,
            menu=menu,
            name="Z current name",
            price=10,
        )
        for name, quantity in (("A old name", 2), ("Z current name", 3)):
            order = self.create_order(
                status=Order.Status.COMPLETED,
                payment_status=Order.PaymentStatus.PAID,
            )
            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                menu_item_name=name,
                quantity=quantity,
                unit_price=10,
                total_price=10 * quantity,
            )

        archived_order = self.create_order(
            status=Order.Status.COMPLETED,
            payment_status=Order.PaymentStatus.PAID,
        )
        OrderItem.objects.create(
            order=archived_order,
            menu_item=None,
            menu_item_name="Archived dish",
            quantity=4,
            unit_price=5,
            total_price=20,
        )

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        products = response.data["top_products"]
        self.assertEqual(len(products), 2)
        linked_product = next(p for p in products if p["menu_item"] == menu_item.id)
        archived_product = next(p for p in products if p["menu_item"] is None)
        self.assertEqual(linked_product["total_sold"], 5)
        self.assertEqual(linked_product["menu_item_name"], "Z current name")
        self.assertEqual(archived_product["menu_item_name"], "Archived dish")
        self.assertEqual(archived_product["total_sold"], 4)
        self.assertEqual(Decimal(str(linked_product["revenue"])), Decimal("50.00"))
        self.assertEqual(linked_product["orders_count"], 2)

    def test_order_creation_is_recorded_in_dashboard_activity_feed(self):
        menu = Menu.objects.create(
            business=self.business,
            name="Lunch",
            category="Food",
        )
        menu_item = MenuItem.objects.create(
            business=self.business,
            menu=menu,
            name="Soup",
            price=8,
        )

        order = OrderService.create_order(
            business=self.business,
            validated_data={
                "table": None,
                "order_type": Order.OrderType.TAKEAWAY,
                "items": [{"menu_item_id": menu_item.id, "quantity": 1}],
            },
            user=self.user,
        )
        OrderService.update_status(
            business=self.business,
            order_id=order.id,
            status=Order.Status.COMPLETED,
            payment_status=Order.PaymentStatus.PAID,
            user=self.user,
        )
        OrderService.update_status(
            business=self.business,
            order_id=order.id,
            status=Order.Status.COMPLETED,
            payment_status=Order.PaymentStatus.PAID,
            user=self.user,
        )

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        activities = response.data["activities"]
        self.assertEqual(len(activities), 2)
        self.assertEqual(
            {activity["action"] for activity in activities},
            {"order_created", "order_completed"},
        )
        self.assertTrue(
            all(activity["user"] == self.user.name for activity in activities)
        )

    def test_rejected_paid_order_deletion_does_not_log_success(self):
        order = self.create_order(payment_status=Order.PaymentStatus.PAID)

        with self.assertRaises(ValidationError):
            OrderService.delete_order(order, user=self.user)

        self.assertTrue(Order.objects.filter(pk=order.pk).exists())
        self.assertFalse(ActivityLog.objects.filter(entity_id=order.id).exists())

    def test_failed_order_deletion_rolls_back_activity_record(self):
        order = self.create_order(payment_status=Order.PaymentStatus.PENDING)

        with patch("products.models.Order.delete", side_effect=DatabaseError("delete failed")):
            with self.assertRaises(DatabaseError):
                OrderService.delete_order(order, user=self.user)

        self.assertTrue(Order.objects.filter(pk=order.pk).exists())
        self.assertFalse(ActivityLog.objects.filter(entity_id=order.id).exists())

    def test_activity_log_failure_rolls_back_order_update(self):
        order = self.create_order(notes="before")

        with patch(
            "products.services.order_service.ActivityLogService.record",
            side_effect=DatabaseError("activity insert failed"),
        ):
            with self.assertRaises(DatabaseError):
                OrderService.update_order(
                    business=self.business,
                    order_id=order.id,
                    validated_data={"notes": "after"},
                    user=self.user,
                )

        order.refresh_from_db()
        self.assertEqual(order.notes, "before")
        self.assertFalse(ActivityLog.objects.filter(entity_id=order.id).exists())

    def test_failed_wallet_payment_does_not_log_completion(self):
        customer = Customer.objects.create(
            business=self.business,
            name="Wallet customer",
            phone="8003",
        )
        order = self.create_order(
            customer=customer,
            payment_method=Order.PaymentMethod.CUSTOMER_ACCOUNT,
        )

        with patch(
            "products.services.order_service.WalletService.debit",
            side_effect=ValidationError("debit failed"),
        ):
            with self.assertRaises(ValidationError):
                OrderService.update_status(
                    business=self.business,
                    order_id=order.id,
                    status=Order.Status.COMPLETED,
                    payment_status=Order.PaymentStatus.PAID,
                    user=self.user,
                )

        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)
        self.assertFalse(ActivityLog.objects.filter(entity_id=order.id).exists())
