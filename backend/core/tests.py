from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Role, User
from products.models import Order


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

# Create your tests here.
