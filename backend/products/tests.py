from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Role, User
from products.models import Customer, Order


class OrderListPaginationTests(APITestCase):
    endpoint = "/api/products/orders/list/"

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="orders-pagination@example.com",
            password="password",
            name="Orders Pagination User",
            number="7001",
        )
        self.other_user = User.objects.create_user(
            email="other-orders-pagination@example.com",
            password="password",
            name="Other Orders Pagination User",
            number="7002",
        )
        self.business = Business.objects.create(name="Orders Business")
        self.other_business = Business.objects.create(name="Other Orders Business")
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

    def create_order(self, business=None, **overrides):
        values = {
            "business": business or self.business,
            "order_type": Order.OrderType.DINE_IN,
            "status": Order.Status.PENDING,
            "payment_method": Order.PaymentMethod.CASH,
            "payment_status": Order.PaymentStatus.PENDING,
            "total_amount": 10,
        }
        values.update(overrides)
        return Order.objects.create(**values)

    def test_default_pagination(self) -> None:
        for _ in range(25):
            self.create_order()

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 25)
        self.assertEqual(len(response.data["results"]), 20)
        self.assertIsNone(response.data["previous"])
        self.assertIsNotNone(response.data["next"])

    def test_specific_page_and_page_size(self) -> None:
        for _ in range(15):
            self.create_order()

        response = self.client.get(
            self.endpoint,
            {"page": 2, "page_size": 5},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 15)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertIsNotNone(response.data["previous"])
        self.assertIsNotNone(response.data["next"])

    def test_page_size_is_limited_to_maximum(self) -> None:
        for _ in range(105):
            self.create_order()

        response = self.client.get(
            self.endpoint,
            {"page_size": 1000},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 105)
        self.assertEqual(len(response.data["results"]), 100)

    def test_existing_filters_remain_tenant_scoped(self) -> None:
        customer = Customer.objects.create(
            business=self.business,
            name="Filtered Customer",
            phone="09120000000",
        )
        self.create_order(
            total_amount=100,
            customer=customer,
            order_type=Order.OrderType.TAKEAWAY,
            status=Order.Status.COMPLETED,
            payment_method=Order.PaymentMethod.CARD,
            payment_status=Order.PaymentStatus.PAID,
        )
        self.create_order(
            business=self.other_business,
            total_amount=100,
            order_type=Order.OrderType.TAKEAWAY,
            status=Order.Status.COMPLETED,
            payment_method=Order.PaymentMethod.CARD,
            payment_status=Order.PaymentStatus.PAID,
        )
        today = timezone.localdate().isoformat()

        response = self.client.get(
            self.endpoint,
            {
                "search": "Filtered Customer",
                "status": Order.Status.COMPLETED,
                "order_type": Order.OrderType.TAKEAWAY,
                "payment_status": Order.PaymentStatus.PAID,
                "payment_method": Order.PaymentMethod.CARD,
                "from_date": today,
                "to_date": today,
                "min_total": 100,
                "max_total": 100,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["business"]["id"],
            self.business.id,
        )

# Create your tests here.
