from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Role, User
from products.models import Customer, Menu, MenuItem, Order, OrderItem
from products.services.menu_service import MenuService


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


class HistoricalOrderItemTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="historical-order@example.com",
            password="password",
            name="Historical Order User",
            number="7003",
        )
        self.business = Business.objects.create(name="Historical Orders Business")
        role = Role.objects.create(
            business=self.business,
            name="Owner",
            code="OWNER",
        )
        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=role,
            is_active=True,
        )
        self.client.force_authenticate(self.user)

    def create_historical_order(self):
        menu = Menu.objects.create(
            business=self.business,
            name="Historical Menu",
            category="Main",
        )
        menu_item = MenuItem.objects.create(
            business=self.business,
            menu=menu,
            name="Original Item",
            price="12.50",
        )
        order = Order.objects.create(
            business=self.business,
            order_type=Order.OrderType.DINE_IN,
            status=Order.Status.PENDING,
            payment_method=Order.PaymentMethod.CASH,
            payment_status=Order.PaymentStatus.PENDING,
            subtotal="25.00",
            total_amount="25.00",
        )
        order_item = OrderItem.objects.create(
            order=order,
            menu_item=menu_item,
            menu_item_name="Original Item",
            quantity=2,
            unit_price="12.50",
            total_price="25.00",
            notes="Historical note",
        )
        return menu, menu_item, order, order_item

    def test_deleting_menu_item_preserves_snapshot_and_api_serialization(self):
        _, menu_item, order, order_item = self.create_historical_order()
        original_subtotal = Decimal("25.00")
        original_total = Decimal("25.00")

        menu_item.delete()

        order_item.refresh_from_db()
        order.refresh_from_db()
        self.assertIsNone(order_item.menu_item_id)
        self.assertEqual(order_item.menu_item_name, "Original Item")
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.unit_price, Decimal("12.50"))
        self.assertEqual(order_item.total_price, Decimal("25.00"))
        self.assertEqual(order.subtotal, original_subtotal)
        self.assertEqual(order.total_amount, original_total)

        detail_response = self.client.get(
            f"/api/products/orders/{order.id}/",
        )
        list_response = self.client.get("/api/products/orders/list/")

        for response in (detail_response, list_response):
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            payload = response.data
            if "results" in payload:
                payload = payload["results"][0]
            item = payload["items"][0]
            self.assertIsNone(item["menu_item_id"])
            self.assertEqual(item["menu_item_name"], "Original Item")
            self.assertEqual(item["quantity"], 2)
            self.assertEqual(item["unit_price"], "12.50")
            self.assertEqual(item["total_price"], "25.00")

    def test_deleting_menu_preserves_historical_order_items(self):
        menu, _, order, order_item = self.create_historical_order()
        original_subtotal = Decimal("25.00")
        original_total = Decimal("25.00")

        menu.delete()

        order_item.refresh_from_db()
        order.refresh_from_db()
        self.assertIsNone(order_item.menu_item_id)
        self.assertEqual(order_item.menu_item_name, "Original Item")
        self.assertEqual(order.subtotal, original_subtotal)
        self.assertEqual(order.total_amount, original_total)

    def test_menu_update_removing_item_preserves_historical_order_item(self):
        menu, _, order, order_item = self.create_historical_order()
        original_subtotal = Decimal("25.00")
        original_total = Decimal("25.00")

        MenuService.update_menu(
            menu,
            {"items": []},
        )

        order_item.refresh_from_db()
        order.refresh_from_db()
        self.assertIsNone(order_item.menu_item_id)
        self.assertEqual(order_item.menu_item_name, "Original Item")
        self.assertEqual(order.subtotal, original_subtotal)
        self.assertEqual(order.total_amount, original_total)

# Create your tests here.
