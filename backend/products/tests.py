from decimal import Decimal
from importlib import import_module
from types import SimpleNamespace

from django.utils import timezone
from django.test import TestCase
from unittest.mock import Mock, patch
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Role, User
from products.models import Customer, Menu, MenuItem, Order, OrderItem
from products.models import CustomerAccount, CustomerTransaction
from products.services.menu_service import MenuService
from products.services.order_service import OrderService
from products.services.wallet_service import WalletService
from products.services.customer_service import CustomerService


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


class OrderWalletPaymentTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Wallet Business")
        self.customer = Customer.objects.create(
            business=self.business, name="Wallet Customer", phone="12345"
        )
        self.account = CustomerAccount.objects.create(
            business=self.business, customer=self.customer, balance=Decimal("100.00")
        )
        self.order = Order.objects.create(
            business=self.business,
            customer=self.customer,
            order_type=Order.OrderType.TAKEAWAY,
            payment_method=Order.PaymentMethod.CUSTOMER_ACCOUNT,
            total_amount=Decimal("25.50"),
        )

    def update(self, status=Order.Status.PENDING, **kwargs):
        return OrderService.update_status(
            business=self.business, order_id=self.order.id, status=status, **kwargs
        )

    def test_paid_request_debits_even_before_fulfillment_completion(self):
        self.update(payment_status=Order.PaymentStatus.PAID)
        self.account.refresh_from_db()
        self.order.refresh_from_db()
        txn = CustomerTransaction.objects.get(order=self.order)
        self.assertEqual(self.account.balance, Decimal("74.50"))
        self.assertEqual(txn.type, CustomerTransaction.Type.DEBIT)
        self.assertEqual(txn.account_id, self.account.id)
        self.assertEqual(txn.amount, Decimal("25.50"))
        self.assertEqual(txn.balance_after, self.account.balance)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)

    def test_completion_charges_once_and_repeated_paid_request_is_idempotent(self):
        self.update(status=Order.Status.COMPLETED)
        self.update(status=Order.Status.COMPLETED)
        self.update(status=Order.Status.COMPLETED, payment_status=Order.PaymentStatus.PAID)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("74.50"))
        self.assertEqual(CustomerTransaction.objects.filter(order=self.order, type="debit").count(), 1)

    def test_transaction_failure_rolls_back_balance_and_payment_state(self):
        with patch.object(CustomerTransaction.objects, "create", side_effect=RuntimeError("ledger down")):
            with self.assertRaises(RuntimeError):
                self.update(payment_status=Order.PaymentStatus.PAID)
        self.account.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)
        self.assertFalse(CustomerTransaction.objects.filter(order=self.order).exists())

    def test_order_save_failure_rolls_back_wallet_debit(self):
        original_save = Order.save

        def fail_payment_state_save(instance, *args, **kwargs):
            if (
                instance.pk == self.order.pk
                and kwargs.get("update_fields") == ["payment_status"]
            ):
                raise RuntimeError("order update failed")
            return original_save(instance, *args, **kwargs)

        with patch.object(Order, "save", autospec=True, side_effect=fail_payment_state_save):
            with self.assertRaises(RuntimeError):
                self.update(payment_status=Order.PaymentStatus.PAID)
        self.account.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)
        self.assertFalse(CustomerTransaction.objects.filter(order=self.order).exists())

    def test_payment_method_change_and_paid_request_in_one_call_charges_wallet(self):
        self.order.payment_method = Order.PaymentMethod.CASH
        self.order.save(update_fields=["payment_method"])
        self.update(
            payment_method=Order.PaymentMethod.CUSTOMER_ACCOUNT,
            payment_status=Order.PaymentStatus.PAID,
        )
        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.payment_method, Order.PaymentMethod.CUSTOMER_ACCOUNT)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(self.account.balance, Decimal("74.50"))
        self.assertEqual(CustomerTransaction.objects.filter(order=self.order, type="debit").count(), 1)

    def test_completion_cannot_override_explicit_non_paid_wallet_status(self):
        with self.assertRaises(ValidationError):
            self.update(
                status=Order.Status.COMPLETED,
                payment_status=Order.PaymentStatus.FAILED,
            )
        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertFalse(CustomerTransaction.objects.filter(order=self.order).exists())

    def test_refunded_wallet_order_cannot_be_charged_again(self):
        self.order.payment_status = Order.PaymentStatus.REFUNDED
        self.order.save(update_fields=["payment_status"])
        with self.assertRaises(ValidationError):
            self.update(payment_status=Order.PaymentStatus.PAID)
        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.REFUNDED)
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertFalse(CustomerTransaction.objects.filter(order=self.order).exists())

    def test_customer_account_payment_requires_customer_from_same_business(self):
        self.order.customer = None
        self.order.save(update_fields=["customer"])
        with self.assertRaises(ValidationError):
            self.update(status=Order.Status.COMPLETED)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(self.account.balance, Decimal("100.00"))

    def test_paid_order_cannot_be_financially_edited(self):
        self.update(payment_status=Order.PaymentStatus.PAID)
        with self.assertRaises(ValidationError):
            OrderService.update_order(
                business=self.business,
                order_id=self.order.id,
                validated_data={"discount": Decimal("1.00")},
            )
        self.order.refresh_from_db()
        self.assertEqual(self.order.total_amount, Decimal("25.50"))
        self.assertEqual(self.account.transactions.filter(type="debit").count(), 1)

    def test_existing_paid_marker_without_ledger_is_rejected_for_reconciliation(self):
        self.order.payment_status = Order.PaymentStatus.PAID
        self.order.save(update_fields=["payment_status"])
        with self.assertRaises(ValidationError):
            self.update(payment_status=Order.PaymentStatus.PAID)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertFalse(CustomerTransaction.objects.filter(order=self.order).exists())

    def test_wallet_rejects_customer_from_another_business(self):
        other_business = Business.objects.create(name="Other Wallet Business")
        with self.assertRaises(ValidationError):
            WalletService.debit(
                business=self.business,
                customer=Customer.objects.create(
                    business=other_business, name="Other Customer", phone="54321"
                ),
                amount=Decimal("1.00"),
            )

    def test_paid_wallet_completion_retry_rejects_missing_ledger(self):
        self.order.payment_status = Order.PaymentStatus.PAID
        self.order.save(update_fields=["payment_status"])
        with self.assertRaises(ValidationError):
            self.update(status=Order.Status.COMPLETED)
        self.account.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertFalse(CustomerTransaction.objects.filter(order=self.order).exists())

    def test_paid_wallet_order_with_matching_debit_validates_without_recharging(self):
        self.update(payment_status=Order.PaymentStatus.PAID)
        self.update(status=Order.Status.READY)
        self.update(status=Order.Status.COMPLETED)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("74.50"))
        self.assertEqual(CustomerTransaction.objects.filter(order=self.order, type="debit").count(), 1)

    def test_paid_wallet_order_with_mismatched_debit_fails_closed(self):
        self.order.payment_status = Order.PaymentStatus.PAID
        self.order.save(update_fields=["payment_status"])
        CustomerTransaction.objects.create(
            account=self.account,
            order=self.order,
            type=CustomerTransaction.Type.DEBIT,
            amount=Decimal("10.00"),
            balance_after=Decimal("90.00"),
        )
        with self.assertRaises(ValidationError):
            self.update(status=Order.Status.READY)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertEqual(CustomerTransaction.objects.filter(order=self.order).count(), 1)

    def test_direct_pay_order_call_is_atomic(self):
        with patch.object(CustomerTransaction.objects, "create", side_effect=RuntimeError("ledger down")):
            with self.assertRaises(RuntimeError):
                OrderService.pay_order(order=self.order, business=self.business)
        self.account.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)

    def test_cash_and_card_paid_status_does_not_touch_wallet(self):
        for method in (Order.PaymentMethod.CASH, Order.PaymentMethod.CARD):
            order = Order.objects.create(
                business=self.business,
                customer=self.customer,
                order_type=Order.OrderType.TAKEAWAY,
                payment_method=method,
                total_amount=Decimal("25.50"),
            )
            OrderService.update_status(
                business=self.business,
                order_id=order.id,
                status=Order.Status.PENDING,
                payment_status=Order.PaymentStatus.PAID,
            )
            OrderService.update_status(
                business=self.business,
                order_id=order.id,
                status=Order.Status.COMPLETED,
            )
            order.refresh_from_db()
            self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)
            self.assertFalse(CustomerTransaction.objects.filter(order=order).exists())
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("100.00"))

    def test_deletion_guards_preserve_paid_order_and_wallet_records(self):
        self.update(payment_status=Order.PaymentStatus.PAID)
        with self.assertRaises(ValidationError):
            OrderService.delete_order(self.order)
        with self.assertRaises(ValidationError):
            CustomerService.delete_customer(customer=self.customer)
        self.order.refresh_from_db()
        self.customer.refresh_from_db()
        self.account.refresh_from_db()
        txn = CustomerTransaction.objects.get(order=self.order)
        self.assertEqual(self.account.balance, Decimal("74.50"))
        self.assertEqual(txn.account_id, self.account.id)
        self.assertEqual(txn.order_id, self.order.id)

    def test_paid_card_order_prevents_order_and_customer_deletion(self):
        card_order = Order.objects.create(
            business=self.business,
            customer=self.customer,
            order_type=Order.OrderType.TAKEAWAY,
            payment_method=Order.PaymentMethod.CARD,
            payment_status=Order.PaymentStatus.PAID,
            total_amount=Decimal("25.50"),
        )
        with self.assertRaises(ValidationError):
            OrderService.delete_order(card_order)
        with self.assertRaises(ValidationError):
            CustomerService.delete_customer(customer=self.customer)
        self.assertTrue(Order.objects.filter(pk=card_order.pk).exists())
        self.assertTrue(Customer.objects.filter(pk=self.customer.pk).exists())

    def test_unsettled_order_and_customer_without_wallet_history_can_be_deleted(self):
        order = Order.objects.create(
            business=self.business,
            order_type=Order.OrderType.TAKEAWAY,
        )
        OrderService.delete_order(order)
        self.assertFalse(Order.objects.filter(pk=order.pk).exists())

        customer = Customer.objects.create(
            business=self.business, name="Disposable", phone="98765"
        )
        CustomerService.delete_customer(customer=customer)
        self.assertFalse(Customer.objects.filter(pk=customer.pk).exists())

    def test_debit_below_balance_preserves_existing_debtor_policy(self):
        self.account.balance = Decimal("5.00")
        self.account.save(update_fields=["balance"])
        self.update(payment_status=Order.PaymentStatus.PAID)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("-20.50"))


class WalletDebitMigrationTests(TestCase):
    def test_duplicate_check_fails_with_order_reference_without_mutating_data(self):
        query = Mock()
        query.using.return_value.filter.return_value.values.return_value.annotate.return_value.filter.return_value.first.return_value = {"order_id": 812}
        historical_model = SimpleNamespace(objects=query)
        apps = Mock()
        apps.get_model.return_value = historical_model
        migration = import_module("products.migrations.0015_unique_order_wallet_debit")
        schema_editor = SimpleNamespace(
            connection=SimpleNamespace(alias="default"),
        )

        with self.assertRaisesRegex(RuntimeError, "order 812"):
            migration.reject_existing_duplicate_order_debits(apps, schema_editor)

        apps.get_model.assert_called_once_with("products", "CustomerTransaction")
        query.using.assert_called_once_with("default")
        query.delete.assert_not_called()
