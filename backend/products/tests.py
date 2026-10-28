from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
from importlib import import_module
from threading import Barrier
from types import SimpleNamespace
from unittest import skipUnless
from uuid import uuid4

from django.utils import timezone
from django.db import close_old_connections, connection
from django.test import TestCase, TransactionTestCase
from unittest.mock import Mock, patch
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Permission, Role, RolePermission, User
from core.enums import PermissionCode
from core.models import ActivityLog
from products.models import Customer, Menu, MenuItem, Order, OrderItem
from products.models import CustomerAccount, CustomerTransaction, OrderRefund
from products.services.menu_service import MenuService
from products.services.order_service import OrderService
from products.services.wallet_service import WalletService
from products.services.customer_service import CustomerService
from accounts.services.rbac_initializer import RBACInitializer


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
        update_permission = Permission.objects.create(
            name="Update Orders",
            code=PermissionCode.ORDERS_UPDATE,
        )
        RolePermission.objects.create(role=role, permission=update_permission)
        payment_permission, _ = Permission.objects.get_or_create(
            code=PermissionCode.PAYMENTS_MANAGE,
            defaults={"name": "Manage Payments and Refunds"},
        )
        RolePermission.objects.create(role=role, permission=payment_permission)
        inventory_fulfill_permission, _ = Permission.objects.get_or_create(
            code=PermissionCode.INVENTORY_ORDER_FULFILL,
            defaults={"name": "Fulfill Order Inventory"},
        )
        RolePermission.objects.create(role=role, permission=inventory_fulfill_permission)
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

    def test_direct_pending_to_completed_is_rejected(self) -> None:
        order = self.create_order()

        response = self.client.patch(
            f"/api/products/orders/{order.id}/status/",
            {"status": "completed", "payment_status": "pending", "payment_method": "cash"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)

    def test_status_update_rejects_invalid_status_choice(self) -> None:
        order = self.create_order()

        response = self.client.patch(
            f"/api/products/orders/{order.id}/status/",
            {"status": "COMPLETED"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)

    def test_status_update_rejects_empty_partial_payload(self) -> None:
        order = self.create_order()
        response = self.client.patch(
            f"/api/products/orders/{order.id}/status/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)

    def test_status_payment_and_method_can_be_updated_independently(self) -> None:
        order = self.create_order(status=Order.Status.PREPARING)

        response = self.client.patch(
            f"/api/products/orders/{order.id}/status/",
            {"status": "ready"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.READY)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(order.payment_method, Order.PaymentMethod.CASH)

        response = self.client.patch(
            f"/api/products/orders/{order.id}/status/",
            {"payment_status": "failed"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.READY)
        self.assertEqual(order.payment_status, Order.PaymentStatus.FAILED)
        self.assertEqual(order.payment_method, Order.PaymentMethod.CASH)

        response = self.client.patch(
            f"/api/products/orders/{order.id}/status/",
            {"payment_method": "card"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.READY)
        self.assertEqual(order.payment_status, Order.PaymentStatus.FAILED)
        self.assertEqual(order.payment_method, Order.PaymentMethod.CARD)

    def test_order_mutations_require_existing_orders_update_permission(self) -> None:
        cashier = User.objects.create_user(
            email="orders-cashier@example.com",
            password="password",
            name="Orders Cashier",
            number="7004",
        )
        cashier_role = Role.objects.create(
            business=self.business,
            name="Cashier",
            code="CASHIER",
        )
        Membership.objects.create(
            user=cashier,
            business=self.business,
            role=cashier_role,
            is_active=True,
        )
        order = self.create_order()
        self.client.force_authenticate(cashier)

        status_response = self.client.patch(
            f"/api/products/orders/{order.id}/status/",
            {"status": "completed", "payment_status": "paid", "payment_method": "cash"},
            format="json",
        )
        update_response = self.client.patch(
            f"/api/products/orders/{order.id}/update/",
            {"notes": "Unauthorized edit"},
            format="json",
        )

        self.assertEqual(status_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(update_response.status_code, status.HTTP_403_FORBIDDEN)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)
        self.assertIsNone(order.notes)

    def test_status_update_cannot_mutate_another_business_order(self) -> None:
        order = self.create_order(business=self.other_business)

        response = self.client.patch(
            f"/api/products/orders/{order.id}/status/",
            {"status": "completed", "payment_status": "paid"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)

    def test_failed_cash_payment_can_be_completed_without_marking_it_paid(self) -> None:
        order = self.create_order(
            status=Order.Status.READY,
            payment_status=Order.PaymentStatus.FAILED,
            payment_method=Order.PaymentMethod.CASH,
        )

        response = self.client.patch(
            f"/api/products/orders/{order.id}/status/",
            {"status": "completed", "payment_status": "failed", "payment_method": "cash"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Order.Status.COMPLETED)
        self.assertEqual(response.data["payment_status"], Order.PaymentStatus.FAILED)

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


class OrderFinancialAuthorizationAndRefundApiTests(APITestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Financial API Business")
        self.other_business = Business.objects.create(name="Other Financial Business")
        for permission_code in PermissionCode:
            Permission.objects.get_or_create(
                code=permission_code.value,
                defaults={"name": permission_code.label},
            )
        RBACInitializer.initialize(self.business)
        RBACInitializer.initialize(self.other_business)
        self.customer = Customer.objects.create(
            business=self.business, name="Refund Customer", phone="6001"
        )
        self.account = CustomerAccount.objects.create(
            business=self.business,
            customer=self.customer,
            balance=Decimal("100.00"),
            ledger_opening_balance=Decimal("100.00"),
            ledger_opening_balance_verified=True,
        )
        self.order = Order.objects.create(
            business=self.business,
            customer=self.customer,
            order_type=Order.OrderType.TAKEAWAY,
            payment_method=Order.PaymentMethod.CUSTOMER_ACCOUNT,
            total_amount=Decimal("25.50"),
        )

    def user_for(self, role_code, business=None):
        business = business or self.business
        user = User.objects.create_user(
            email=f"{role_code.lower()}-{business.id}@example.com",
            password="password",
            number=str(7000 + User.objects.count()),
        )
        role = Role.objects.get(business=business, code=role_code)
        Membership.objects.create(
            user=user, business=business, role=role, is_active=True
        )
        return user

    def test_owner_manager_and_accountant_can_manage_payment_fields(self):
        for role_code in ("OWNER", "MANAGER", "ACCOUNTANT"):
            with self.subTest(role=role_code):
                user = self.user_for(role_code)
                self.client.force_authenticate(user)
                response = self.client.patch(
                    f"/api/products/orders/{self.order.id}/status/",
                    {"payment_method": "cash"},
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.order.refresh_from_db()
                self.assertEqual(self.order.payment_method, Order.PaymentMethod.CASH)
                # Reset for the next role without crossing a wallet settlement.
                self.order.payment_method = Order.PaymentMethod.CUSTOMER_ACCOUNT
                self.order.payment_status = Order.PaymentStatus.PENDING
                self.order.save(update_fields=["payment_method", "payment_status"])

    def test_accountant_can_update_payment_only_but_not_status_or_combined_fields(self):
        user = self.user_for("ACCOUNTANT")
        self.client.force_authenticate(user)

        payment_response = self.client.patch(
            f"/api/products/orders/{self.order.id}/status/",
            {"payment_status": "paid"},
            format="json",
        )
        self.assertEqual(payment_response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)

        status_response = self.client.patch(
            f"/api/products/orders/{self.order.id}/status/",
            {"status": "ready"},
            format="json",
        )
        combined_response = self.client.patch(
            f"/api/products/orders/{self.order.id}/status/",
            {"status": "completed", "payment_status": "paid"},
            format="json",
        )
        self.assertEqual(status_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(combined_response.status_code, status.HTTP_403_FORBIDDEN)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)

    def test_chef_can_update_order_status(self):
        user = self.user_for("CHEF")
        self.client.force_authenticate(user)
        self.order.status = Order.Status.PREPARING
        self.order.save(update_fields=("status",))
        response = self.client.patch(
            f"/api/products/orders/{self.order.id}/status/",
            {"status": "ready"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.READY)

    def test_me_response_exposes_active_membership_permissions(self):
        user = self.user_for("ACCOUNTANT")
        self.client.force_authenticate(user)
        response = self.client.get("/api/accounts/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            PermissionCode.PAYMENTS_MANAGE,
            response.data["active_business"]["permissions"],
        )
        self.assertNotIn(
            PermissionCode.ORDERS_UPDATE,
            response.data["active_business"]["permissions"],
        )

    def test_role_initializer_preserves_extra_default_role_permissions(self):
        accountant = Role.objects.get(business=self.business, code="ACCOUNTANT")
        extra_permission = Permission.objects.get(code=PermissionCode.PRODUCTS_DELETE)
        RolePermission.objects.create(role=accountant, permission=extra_permission)

        RBACInitializer.initialize(self.business)

        accountant_permissions = set(
            accountant.role_permissions.values_list("permission__code", flat=True)
        )
        self.assertTrue({
            PermissionCode.REPORTS_VIEW_SALES,
            PermissionCode.PAYMENTS_MANAGE,
            PermissionCode.PRODUCTS_DELETE,
        }.issubset(accountant_permissions))

    def test_chef_combined_status_and_payment_update_is_denied(self):
        user = self.user_for("CHEF")
        self.client.force_authenticate(user)

        response = self.client.patch(
            f"/api/products/orders/{self.order.id}/status/",
            {"status": "ready", "payment_status": "paid"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)

    def test_custom_role_with_orders_update_but_no_inventory_fulfill_cannot_change_status(self):
        user = User.objects.create_user(
            email="custom-order-updater@example.com",
            password="password",
            number=str(7000 + User.objects.count()),
        )
        role = Role.objects.create(
            business=self.business,
            name="Custom Order Updater",
            code="CUSTOM_ORDER_UPDATER",
        )
        Membership.objects.create(user=user, business=self.business, role=role, is_active=True)
        permission = Permission.objects.get(code=PermissionCode.ORDERS_UPDATE)
        RolePermission.objects.create(role=role, permission=permission)
        self.client.force_authenticate(user)
        self.order.status = Order.Status.PREPARING
        self.order.save(update_fields=("status",))

        response = self.client.patch(
            f"/api/products/orders/{self.order.id}/status/",
            {"status": "ready"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PREPARING)

    def test_owner_manager_and_accountant_can_confirm_refunds(self):
        for role_code in ("OWNER", "MANAGER", "ACCOUNTANT"):
            with self.subTest(role=role_code):
                user = self.user_for(role_code)
                order = Order.objects.create(
                    business=self.business,
                    customer=self.customer,
                    order_type=Order.OrderType.TAKEAWAY,
                    payment_method=Order.PaymentMethod.CUSTOMER_ACCOUNT,
                    payment_status=Order.PaymentStatus.PENDING,
                    total_amount=Decimal("25.50"),
                )
                self.client.force_authenticate(user)
                paid = self.client.patch(
                    f"/api/products/orders/{order.id}/status/",
                    {"payment_status": "paid"},
                    format="json",
                )
                self.assertEqual(paid.status_code, status.HTTP_200_OK)
                response = self.client.post(
                    f"/api/products/orders/{order.id}/refund/",
                    {
                        "idempotency_key": str(uuid4()),
                        "reason": "Confirmed wallet return",
                    },
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(OrderRefund.objects.get(order=order).actor_id, user.id)
                recovered = self.client.get(
                    f"/api/products/orders/{order.id}/refund/"
                )
                self.assertEqual(recovered.status_code, status.HTTP_200_OK)
                self.assertEqual(recovered.data["id"], response.data["id"])

    def test_nonapproved_role_with_financial_permission_is_still_denied(self):
        user = User.objects.create_user(
            email="custom-financial-role@example.com",
            password="password",
            number=str(7000 + User.objects.count()),
        )
        role = Role.objects.create(
            business=self.business, name="Custom Finance", code="CUSTOM_FINANCE"
        )
        Membership.objects.create(user=user, business=self.business, role=role, is_active=True)
        permission = Permission.objects.get(code=PermissionCode.PAYMENTS_MANAGE)
        RolePermission.objects.create(role=role, permission=permission)
        order_permission = Permission.objects.get(code=PermissionCode.ORDERS_UPDATE)
        RolePermission.objects.create(role=role, permission=order_permission)
        self.client.force_authenticate(user)

        payment_response = self.client.patch(
            f"/api/products/orders/{self.order.id}/status/",
            {"payment_status": "paid"},
            format="json",
        )
        refund_response = self.client.post(
            f"/api/products/orders/{self.order.id}/refund/",
            {"idempotency_key": str(uuid4()), "reason": "Unauthorized"},
            format="json",
        )
        refund_lookup_response = self.client.get(
            f"/api/products/orders/{self.order.id}/refund/"
        )
        balance_response = self.client.post(
            f"/api/products/customers/{self.customer.id}/credit/",
            {"amount": "5.00", "description": "Unauthorized"},
            format="json",
        )
        financial_edit_response = self.client.patch(
            f"/api/products/orders/{self.order.id}/update/",
            {"discount": "1.00"},
            format="json",
        )

        self.assertEqual(payment_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(refund_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(refund_lookup_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(balance_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(financial_edit_response.status_code, status.HTTP_403_FORBIDDEN)
        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(self.account.balance, Decimal("100.00"))

    def test_reusing_refund_key_with_conflicting_parameters_is_rejected(self):
        self.update_payment_and_authenticate_accountant()
        key = uuid4()
        payload = {"idempotency_key": str(key), "reason": "Order returned"}
        first = self.client.post(
            f"/api/products/orders/{self.order.id}/refund/", payload, format="json"
        )
        retry = self.client.post(
            f"/api/products/orders/{self.order.id}/refund/", payload, format="json"
        )
        conflicting = self.client.post(
            f"/api/products/orders/{self.order.id}/refund/",
            {**payload, "reason": "Different intent"},
            format="json",
        )
        conflicting_amount = self.client.post(
            f"/api/products/orders/{self.order.id}/refund/",
            {**payload, "amount": "12.00"},
            format="json",
        )
        other_order = Order.objects.create(
            business=self.business,
            customer=self.customer,
            order_type=Order.OrderType.TAKEAWAY,
            payment_method=Order.PaymentMethod.CUSTOMER_ACCOUNT,
            payment_status=Order.PaymentStatus.PAID,
            total_amount=Decimal("25.50"),
        )
        conflicting_order = self.client.post(
            f"/api/products/orders/{other_order.id}/refund/",
            payload,
            format="json",
        )
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(retry.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data["id"], retry.data["id"])
        self.assertEqual(conflicting.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(conflicting_amount.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(conflicting_order.status_code, status.HTTP_400_BAD_REQUEST)

    def update_payment_and_authenticate_accountant(self):
        user = self.user_for("ACCOUNTANT")
        self.client.force_authenticate(user)
        paid = self.client.patch(
            f"/api/products/orders/{self.order.id}/status/",
            {"payment_status": "paid"},
            format="json",
        )
        self.assertEqual(paid.status_code, status.HTTP_200_OK)

    def test_chef_cashier_waiter_cannot_change_payment_fields_or_refund(self):
        for role_code in ("CHEF", "CASHIER", "WAITER"):
            with self.subTest(role=role_code):
                user = self.user_for(role_code)
                self.client.force_authenticate(user)
                response = self.client.patch(
                    f"/api/products/orders/{self.order.id}/status/",
                    {"payment_status": "paid"},
                    format="json",
                )
                refund_response = self.client.post(
                    f"/api/products/orders/{self.order.id}/refund/",
                    {
                        "idempotency_key": str(uuid4()),
                        "reason": "Unauthorized refund",
                    },
                    format="json",
                )
                refund_lookup_response = self.client.get(
                    f"/api/products/orders/{self.order.id}/refund/"
                )
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
                self.assertEqual(refund_response.status_code, status.HTTP_403_FORBIDDEN)
                self.assertEqual(refund_lookup_response.status_code, status.HTTP_403_FORBIDDEN)
                self.order.refresh_from_db()
                self.account.refresh_from_db()
                self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)
                self.assertEqual(self.account.balance, Decimal("100.00"))

    def test_chef_generic_order_update_cannot_change_financial_fields(self):
        user = self.user_for("CHEF")
        self.client.force_authenticate(user)
        notes_response = self.client.patch(
            f"/api/products/orders/{self.order.id}/update/",
            {"notes": "Kitchen note"},
            format="json",
        )
        financial_response = self.client.patch(
            f"/api/products/orders/{self.order.id}/update/",
            {"discount": "1.00"},
            format="json",
        )
        self.assertEqual(notes_response.status_code, status.HTTP_200_OK)
        self.assertEqual(financial_response.status_code, status.HTTP_403_FORBIDDEN)
        self.order.refresh_from_db()
        self.assertEqual(self.order.notes, "Kitchen note")
        self.assertEqual(self.order.discount, Decimal("0.00"))

    def test_chef_cannot_use_direct_wallet_balance_endpoint(self):
        user = self.user_for("CHEF")
        self.client.force_authenticate(user)
        response = self.client.post(
            f"/api/products/customers/{self.customer.id}/debit/",
            {"amount": "5.00", "description": "Direct API attempt"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("100.00"))

    def test_unauthenticated_payment_change_is_denied(self):
        response = self.client.patch(
            f"/api/products/orders/{self.order.id}/status/",
            {"payment_status": "paid"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        refund_lookup = self.client.get(
            f"/api/products/orders/{self.order.id}/refund/"
        )
        self.assertEqual(refund_lookup.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cross_business_refund_cannot_reach_order_or_wallet(self):
        user = self.user_for("ACCOUNTANT")
        other_order = Order.objects.create(
            business=self.other_business,
            order_type=Order.OrderType.TAKEAWAY,
            payment_method=Order.PaymentMethod.CASH,
            payment_status=Order.PaymentStatus.PAID,
            total_amount=Decimal("10.00"),
        )
        self.client.force_authenticate(user)
        response = self.client.post(
            f"/api/products/orders/{other_order.id}/refund/",
            {
                "idempotency_key": str(uuid4()),
                "reason": "Cross tenant attempt",
                "amount": "10.00",
                "confirm_external_refund": True,
            },
            format="json",
        )
        lookup_response = self.client.get(
            f"/api/products/orders/{other_order.id}/refund/"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(lookup_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(OrderRefund.objects.filter(order=other_order).exists())

    def test_wallet_refund_api_is_auditable_and_rejects_status_only_refund(self):
        user = self.user_for("ACCOUNTANT")
        self.client.force_authenticate(user)
        paid = self.client.patch(
            f"/api/products/orders/{self.order.id}/status/",
            {"payment_status": "paid"},
            format="json",
        )
        self.assertEqual(paid.status_code, status.HTTP_200_OK)
        status_only = self.client.patch(
            f"/api/products/orders/{self.order.id}/status/",
            {"payment_status": "refunded"},
            format="json",
        )
        self.assertEqual(status_only.status_code, status.HTTP_400_BAD_REQUEST)
        key = uuid4()
        payload = {
            "idempotency_key": str(key),
            "reason": "Order returned",
        }
        # Simulate the client losing the successful POST response and recovering
        # the durable receipt by order after a reload.
        self.client.post(
            f"/api/products/orders/{self.order.id}/refund/", payload, format="json"
        )
        recovered = self.client.get(
            f"/api/products/orders/{self.order.id}/refund/"
        )
        retry = self.client.post(
            f"/api/products/orders/{self.order.id}/refund/", payload, format="json"
        )
        self.assertEqual(retry.status_code, status.HTTP_200_OK)
        self.assertEqual(recovered.status_code, status.HTTP_200_OK)
        self.assertEqual(recovered["Cache-Control"], "no-store")
        self.assertEqual(recovered.data["amount"], Decimal("25.50"))
        self.assertEqual(recovered.data["id"], retry.data["id"])
        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CANCELLED)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.REFUNDED)
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertEqual(
            CustomerTransaction.objects.filter(
                order=self.order,
                type=CustomerTransaction.Type.CREDIT,
                is_order_settlement=True,
            ).count(),
            1,
        )
        refund_credit = CustomerTransaction.objects.get(
            order=self.order,
            type=CustomerTransaction.Type.CREDIT,
            is_order_settlement=True,
        )
        self.assertEqual(refund_credit.refund_id, recovered.data["id"])

    def test_order_linked_wallet_credit_requires_explicit_refund_record(self):
        with self.assertRaises(ValidationError):
            WalletService.credit(
                business=self.business,
                customer=self.customer,
                amount=Decimal("5.00"),
                order=self.order,
                description="Attempted direct reversal",
            )
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertFalse(CustomerTransaction.objects.filter(order=self.order).exists())

    def test_cash_card_refund_cannot_be_finalized_without_payment_evidence(self):
        user = self.user_for("MANAGER")
        self.order.payment_method = Order.PaymentMethod.CARD
        self.order.payment_status = Order.PaymentStatus.PAID
        self.order.save(update_fields=["payment_method", "payment_status"])
        self.client.force_authenticate(user)
        payload = {
            "idempotency_key": str(uuid4()),
            "reason": "Card charge reversed",
            "amount": "25.50",
            "reference": "processor-ref-123",
        }
        status_only = self.client.patch(
            f"/api/products/orders/{self.order.id}/status/",
            {"payment_status": "refunded"},
            format="json",
        )
        missing_confirmation = self.client.post(
            f"/api/products/orders/{self.order.id}/refund/", payload, format="json"
        )
        self.assertEqual(status_only.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(missing_confirmation.status_code, status.HTTP_400_BAD_REQUEST)
        payload["confirm_external_refund"] = True
        attested_without_payment_record = self.client.post(
            f"/api/products/orders/{self.order.id}/refund/", payload, format="json"
        )
        self.assertEqual(attested_without_payment_record.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(OrderRefund.objects.filter(order=self.order).exists())
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)


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


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row-lock semantics")
class OrderRefundPostgresConcurrencyTests(TransactionTestCase):
    """Exercise concurrent refund retries using independent DB connections."""

    def setUp(self):
        self.business = Business.objects.create(name="Concurrent Refund Business")
        self.customer = Customer.objects.create(
            business=self.business, name="Concurrent Refund Customer", phone="99001"
        )
        self.account = CustomerAccount.objects.create(
            business=self.business,
            customer=self.customer,
            balance=Decimal("100.00"),
            ledger_opening_balance=Decimal("100.00"),
            ledger_opening_balance_verified=True,
        )
        self.order = Order.objects.create(
            business=self.business,
            customer=self.customer,
            order_type=Order.OrderType.TAKEAWAY,
            payment_method=Order.PaymentMethod.CUSTOMER_ACCOUNT,
            payment_status=Order.PaymentStatus.PENDING,
            total_amount=Decimal("25.50"),
        )
        self.user = User.objects.create_user(
            email="concurrent-refund@example.com",
            password="password",
            name="Concurrent Refund Actor",
            number="99002",
        )
        OrderService.pay_order(order=self.order, business=self.business)

    def test_concurrent_same_key_refunds_create_one_credit(self):
        key = uuid4()
        gate = Barrier(2)

        def refund_once():
            close_old_connections()
            try:
                gate.wait(timeout=10)
                return OrderService.refund_order(
                    business=self.business,
                    order_id=self.order.id,
                    user=self.user,
                    idempotency_key=key,
                    reason="Concurrent retry",
                )
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: refund_once(), range(2)))

        self.assertEqual(results[0].id, results[1].id)
        self.assertEqual(OrderRefund.objects.filter(order=self.order).count(), 1)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertEqual(
            CustomerTransaction.objects.filter(
                order=self.order,
                type=CustomerTransaction.Type.CREDIT,
                refund__isnull=False,
            ).count(),
            1,
        )


class OrderWalletPaymentTests(TestCase):
    def setUp(self):
        self.actor = User.objects.create_user(
            email="wallet-order-actor@example.test", password="test-password",
            name="Wallet Operator", number="7006",
        )
        self.business = Business.objects.create(name="Wallet Business")
        self.customer = Customer.objects.create(
            business=self.business, name="Wallet Customer", phone="12345"
        )
        self.account = CustomerAccount.objects.create(
            business=self.business,
            customer=self.customer,
            balance=Decimal("100.00"),
            ledger_opening_balance=Decimal("100.00"),
            ledger_opening_balance_verified=True,
        )
        self.menu = Menu.objects.create(
            business=self.business, name="Wallet Menu", category="Test"
        )
        self.menu_item = MenuItem.objects.create(
            business=self.business,
            menu=self.menu,
            name="Wallet Item",
            price=Decimal("25.50"),
        )
        self.order = Order.objects.create(
            business=self.business,
            customer=self.customer,
            order_type=Order.OrderType.TAKEAWAY,
            payment_method=Order.PaymentMethod.CUSTOMER_ACCOUNT,
            total_amount=Decimal("25.50"),
        )

    def update(self, status=None, **kwargs):
        return OrderService.update_status(
            business=self.business, order_id=self.order.id, status=status, user=self.actor, **kwargs
        )

    def complete_order(self, **kwargs):
        """Wallet tests use empty legacy orders; place them at ready before completion."""
        self.order.refresh_from_db()
        if self.order.status == Order.Status.PENDING:
            self.order.status = Order.Status.PREPARING
            self.order.save(update_fields=("status",))
        if self.order.status == Order.Status.PREPARING:
            self.update(status=Order.Status.READY)
        return self.update(status=Order.Status.COMPLETED, **kwargs)

    def edit_order_price(self, amount):
        self.menu_item.price = amount
        self.menu_item.save(update_fields=["price"])
        return OrderService.update_order(
            business=self.business,
            order_id=self.order.id,
            validated_data={
                "items": [{"menu_item_id": self.menu_item.id, "quantity": 1}]
            },
        )

    def record_refund(self, *, amount=None, confirm_external_refund=False, key=None):
        return OrderService.refund_order(
            business=self.business,
            order_id=self.order.id,
            user=None,
            idempotency_key=key or uuid4(),
            reason="Customer requested a refund",
            amount=amount,
            confirm_external_refund=confirm_external_refund,
        )

    def test_paid_cash_and_card_orders_reject_financial_edits(self):
        other_customer = Customer.objects.create(
            business=self.business, name="Other Customer", phone="54321"
        )
        financial_edits = (
            {"items": [{"menu_item_id": self.menu_item.id, "quantity": 1}]},
            {"customer": other_customer},
            {"discount": Decimal("1.00")},
            {"tax": Decimal("1.00")},
        )

        for payment_method in (Order.PaymentMethod.CASH, Order.PaymentMethod.CARD):
            with self.subTest(payment_method=payment_method):
                self.order.payment_method = payment_method
                self.order.payment_status = Order.PaymentStatus.PAID
                self.order.save(update_fields=["payment_method", "payment_status"])

                for validated_data in financial_edits:
                    with self.subTest(validated_data=validated_data):
                        with self.assertRaises(ValidationError):
                            OrderService.update_order(
                                business=self.business,
                                order_id=self.order.id,
                                validated_data=validated_data.copy(),
                            )

                self.order.refresh_from_db()
                self.assertEqual(self.order.customer, self.customer)
                self.assertEqual(self.order.total_amount, Decimal("25.50"))
                self.assertFalse(self.order.items.exists())

    def test_paid_cash_and_card_orders_allow_nonfinancial_edits(self):
        for payment_method in (Order.PaymentMethod.CASH, Order.PaymentMethod.CARD):
            with self.subTest(payment_method=payment_method):
                self.order.payment_method = payment_method
                self.order.payment_status = Order.PaymentStatus.PAID
                self.order.save(update_fields=["payment_method", "payment_status"])

                OrderService.update_order(
                    business=self.business,
                    order_id=self.order.id,
                    validated_data={"notes": "Leave at reception"},
                )

                self.order.refresh_from_db()
                self.assertEqual(self.order.notes, "Leave at reception")
                self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)

    def test_cash_and_card_refund_is_rejected_without_immutable_payment_record(self):
        for payment_method in (Order.PaymentMethod.CASH, Order.PaymentMethod.CARD):
            with self.subTest(payment_method=payment_method):
                self.order.payment_method = payment_method
                self.order.payment_status = Order.PaymentStatus.PAID
                self.order.save(update_fields=["payment_method", "payment_status"])
                with self.assertRaises(ValidationError):
                    self.record_refund(
                        amount=self.order.total_amount,
                        confirm_external_refund=True,
                    )

                self.order.refresh_from_db()
                self.assertEqual(self.order.total_amount, Decimal("25.50"))
                self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
                self.assertFalse(OrderRefund.objects.filter(order=self.order).exists())

    def test_cash_and_card_refund_does_not_trust_changed_current_order_total(self):
        for payment_method in (Order.PaymentMethod.CASH, Order.PaymentMethod.CARD):
            with self.subTest(payment_method=payment_method):
                self.order.payment_method = payment_method
                self.order.payment_status = Order.PaymentStatus.PAID
                self.order.total_amount = Decimal("31.00")
                self.order.save(update_fields=["payment_method", "payment_status", "total_amount"])
                with self.assertRaises(ValidationError):
                    self.record_refund(
                        amount=self.order.total_amount,
                        confirm_external_refund=True,
                    )
                self.order.refresh_from_db()
                self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
                self.assertFalse(OrderRefund.objects.filter(order=self.order).exists())

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

    def test_preparing_and_ready_orders_can_be_completed(self):
        for initial_status in (Order.Status.PREPARING, Order.Status.READY):
            with self.subTest(initial_status=initial_status):
                self.order.status = initial_status
                self.order.payment_method = Order.PaymentMethod.CASH
                self.order.payment_status = Order.PaymentStatus.PENDING
                self.order.save(update_fields=["status", "payment_method", "payment_status"])

                if initial_status == Order.Status.PREPARING:
                    self.update(status=Order.Status.READY)
                self.update(status=Order.Status.COMPLETED)

                self.order.refresh_from_db()
                self.assertEqual(self.order.status, Order.Status.COMPLETED)
                self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)
        self.assertFalse(CustomerTransaction.objects.filter(order=self.order).exists())

    def test_failed_wallet_payment_stays_failed_when_only_completing_order(self):
        self.order.payment_status = Order.PaymentStatus.FAILED
        self.order.save(update_fields=["payment_status"])

        self.complete_order()

        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.COMPLETED)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.FAILED)
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertFalse(CustomerTransaction.objects.filter(order=self.order).exists())

    def test_failed_wallet_retry_rolls_back_completion_debit_and_activity_on_error(self):
        self.order.status = Order.Status.PREPARING
        self.order.payment_status = Order.PaymentStatus.FAILED
        self.order.save(update_fields=["status", "payment_status"])
        self.update(status=Order.Status.READY)
        original_settle = WalletService.settle_order

        def settle_then_fail(**kwargs):
            original_settle(**kwargs)
            raise RuntimeError("wallet operation failed after debit")

        with patch.object(WalletService, "settle_order", side_effect=settle_then_fail):
            with self.assertRaisesRegex(RuntimeError, "wallet operation failed"):
                self.update(
                    status=Order.Status.COMPLETED,
                    payment_status=Order.PaymentStatus.PAID,
                )

        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.READY)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.FAILED)
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertFalse(CustomerTransaction.objects.filter(
            order=self.order, type=CustomerTransaction.Type.DEBIT
        ).exists())
        self.assertFalse(ActivityLog.objects.filter(
            entity_type="order", entity_id=self.order.id
        ).exists())

    def test_failed_cash_payment_does_not_prevent_order_completion(self):
        self.order.payment_method = Order.PaymentMethod.CASH
        self.order.payment_status = Order.PaymentStatus.FAILED
        self.order.save(update_fields=["payment_method", "payment_status"])

        self.complete_order()

        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.COMPLETED)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.FAILED)
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertFalse(CustomerTransaction.objects.filter(order=self.order).exists())

    def test_completion_charges_once_and_repeated_paid_request_is_idempotent(self):
        self.complete_order()
        self.complete_order()
        self.complete_order(payment_status=Order.PaymentStatus.PAID)
        self.account.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("74.50"))
        self.assertEqual(self.order.status, Order.Status.COMPLETED)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
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
                and "payment_status" in (kwargs.get("update_fields") or ())
                and instance.payment_status == Order.PaymentStatus.PAID
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

    def test_switching_into_customer_account_requires_explicit_paid_state(self):
        self.order.payment_method = Order.PaymentMethod.CASH
        self.order.payment_status = Order.PaymentStatus.PAID
        self.order.save(update_fields=["payment_method", "payment_status"])

        self.update(payment_method=Order.PaymentMethod.CUSTOMER_ACCOUNT)
        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.payment_method, Order.PaymentMethod.CUSTOMER_ACCOUNT)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertFalse(CustomerTransaction.objects.filter(order=self.order).exists())

        self.update(payment_status=Order.PaymentStatus.PAID)
        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(self.account.balance, Decimal("74.50"))

    def test_cash_and_card_method_switches_do_not_touch_wallet_or_paid_state(self):
        for old_method, new_method in (
            (Order.PaymentMethod.CASH, Order.PaymentMethod.CARD),
            (Order.PaymentMethod.CARD, Order.PaymentMethod.CASH),
        ):
            with self.subTest(old_method=old_method, new_method=new_method):
                self.order.payment_method = old_method
                self.order.payment_status = Order.PaymentStatus.PAID
                self.order.save(update_fields=["payment_method", "payment_status"])

                self.update(payment_method=new_method)

                self.order.refresh_from_db()
                self.account.refresh_from_db()
                self.assertEqual(self.order.payment_method, new_method)
                self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
                self.assertEqual(self.account.balance, Decimal("100.00"))
                self.assertFalse(CustomerTransaction.objects.filter(order=self.order).exists())

    def test_switching_away_from_settled_wallet_is_rejected_without_refund(self):
        self.update(payment_status=Order.PaymentStatus.PAID)

        with self.assertRaises(ValidationError):
            self.update(payment_method=Order.PaymentMethod.CARD)
        with self.assertRaises(ValidationError):
            self.update(
                payment_method=Order.PaymentMethod.CARD,
                payment_status=Order.PaymentStatus.UNPAID,
            )

        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.payment_method, Order.PaymentMethod.CUSTOMER_ACCOUNT)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(self.account.balance, Decimal("74.50"))
        settlements = CustomerTransaction.objects.filter(
            order=self.order, is_order_settlement=True
        )
        self.assertEqual(settlements.count(), 1)
        self.assertEqual(
            sum(
                (txn.amount if txn.type == CustomerTransaction.Type.DEBIT else -txn.amount)
                for txn in settlements
            ),
            Decimal("25.50"),
        )
        self.assertFalse(CustomerTransaction.objects.filter(
            order=self.order, type=CustomerTransaction.Type.CREDIT
        ).exists())

    def test_wallet_refund_adds_compensating_credit_once_and_retries_idempotently(self):
        self.update(payment_status=Order.PaymentStatus.PAID)
        key = uuid4()
        refund = self.record_refund(key=key)
        repeated = self.record_refund(key=key)

        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(refund.id, repeated.id)
        self.assertEqual(refund.amount, Decimal("25.50"))
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.REFUNDED)
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertEqual(
            CustomerTransaction.objects.filter(
                order=self.order,
                type=CustomerTransaction.Type.CREDIT,
                is_order_settlement=True,
            ).count(),
            1,
        )
        refund_credit = CustomerTransaction.objects.get(refund=refund)
        self.assertEqual(refund_credit.order_id, self.order.id)
        self.assertEqual(refund_credit.account_id, self.account.id)
        self.assertEqual(refund_credit.amount, refund.amount)

    def test_partial_wallet_refund_is_rejected_without_cancelling_order(self):
        self.update(payment_status=Order.PaymentStatus.PAID)

        with self.assertRaises(ValidationError):
            self.record_refund(amount=Decimal("10.00"))

        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(self.account.balance, Decimal("74.50"))
        self.assertFalse(OrderRefund.objects.filter(order=self.order).exists())
        self.assertFalse(
            CustomerTransaction.objects.filter(
                order=self.order,
                type=CustomerTransaction.Type.CREDIT,
                is_order_settlement=True,
            ).exists()
        )

    def test_refund_exception_rolls_back_cancellation_and_accounting(self):
        self.update(payment_status=Order.PaymentStatus.PAID)

        with patch(
            "products.services.order_service.ActivityLogService.record",
            side_effect=RuntimeError("refund audit failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "refund audit failed"):
                self.record_refund()

        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(self.account.balance, Decimal("74.50"))
        self.assertFalse(OrderRefund.objects.filter(order=self.order).exists())
        self.assertEqual(
            CustomerTransaction.objects.filter(
                order=self.order,
                type=CustomerTransaction.Type.CREDIT,
                is_order_settlement=True,
            ).count(),
            0,
        )
        self.assertFalse(
            ActivityLog.objects.filter(
                action=ActivityLog.Action.ORDER_REFUNDED,
                entity_type="order",
                entity_id=self.order.id,
            ).exists()
        )

    def test_order_settlement_credit_without_refund_link_fails_closed(self):
        self.account.balance = Decimal("110.00")
        self.account.save(update_fields=["balance"])
        CustomerTransaction.objects.create(
            account=self.account,
            order=self.order,
            type=CustomerTransaction.Type.CREDIT,
            amount=Decimal("10.00"),
            balance_after=Decimal("110.00"),
            is_order_settlement=True,
            is_order_settlement_verified=True,
        )

        with self.assertRaisesRegex(ValidationError, "no refund record"):
            OrderService._validated_order_settlement(order=self.order, business=self.business)

    def test_order_settlement_credit_rejects_refund_for_another_order(self):
        another_order = Order.objects.create(
            business=self.business,
            customer=self.customer,
            order_type=Order.OrderType.TAKEAWAY,
            payment_method=Order.PaymentMethod.CUSTOMER_ACCOUNT,
            total_amount=Decimal("10.00"),
        )
        refund = OrderRefund.objects.create(
            order=another_order,
            business=self.business,
            customer=self.customer,
            payment_method=Order.PaymentMethod.CUSTOMER_ACCOUNT,
            amount=Decimal("10.00"),
            reason="Other order refund",
            idempotency_key=uuid4(),
        )
        self.account.balance = Decimal("110.00")
        self.account.save(update_fields=["balance"])
        CustomerTransaction.objects.create(
            account=self.account,
            order=self.order,
            type=CustomerTransaction.Type.CREDIT,
            amount=Decimal("10.00"),
            balance_after=Decimal("110.00"),
            is_order_settlement=True,
            is_order_settlement_verified=True,
            refund=refund,
        )

        with self.assertRaisesRegex(ValidationError, "does not match"):
            OrderService._validated_order_settlement(order=self.order, business=self.business)

    def test_order_settlement_credit_rejects_mismatched_refund_amount(self):
        refund = OrderRefund.objects.create(
            order=self.order,
            business=self.business,
            customer=self.customer,
            payment_method=Order.PaymentMethod.CUSTOMER_ACCOUNT,
            amount=Decimal("9.00"),
            reason="Mismatched amount",
            idempotency_key=uuid4(),
        )
        self.account.balance = Decimal("110.00")
        self.account.save(update_fields=["balance"])
        CustomerTransaction.objects.create(
            account=self.account,
            order=self.order,
            type=CustomerTransaction.Type.CREDIT,
            amount=Decimal("10.00"),
            balance_after=Decimal("110.00"),
            is_order_settlement=True,
            is_order_settlement_verified=True,
            refund=refund,
        )

        with self.assertRaisesRegex(ValidationError, "does not match"):
            OrderService._validated_order_settlement(order=self.order, business=self.business)

    def test_wallet_completion_allows_explicit_pending_and_unpaid_statuses(self):
        for payment_status in (
            Order.PaymentStatus.PENDING,
            Order.PaymentStatus.UNPAID,
        ):
            with self.subTest(payment_status=payment_status):
                self.complete_order(payment_status=payment_status)
                self.order.refresh_from_db()
                self.account.refresh_from_db()
                self.assertEqual(self.order.status, Order.Status.COMPLETED)
                self.assertEqual(self.order.payment_status, payment_status)
                self.assertEqual(self.account.balance, Decimal("100.00"))
                self.assertFalse(CustomerTransaction.objects.filter(
                    order=self.order, type=CustomerTransaction.Type.DEBIT
                ).exists())

    def test_refunded_wallet_order_cannot_be_charged_again_via_status_update(self):
        self.update(payment_status=Order.PaymentStatus.PAID)
        self.record_refund()
        with self.assertRaises(ValidationError):
            self.update(payment_status=Order.PaymentStatus.PAID)
        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.REFUNDED)
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertEqual(CustomerTransaction.objects.filter(
            order=self.order, type=CustomerTransaction.Type.DEBIT,
            is_order_settlement=True,
        ).count(), 1)

    def test_wallet_refund_amount_comes_from_valid_settlement_history(self):
        self.update(payment_status=Order.PaymentStatus.PAID)
        self.order.total_amount = Decimal("41.00")
        self.order.save(update_fields=["total_amount"])

        refund = self.record_refund()

        self.assertEqual(refund.amount, Decimal("25.50"))
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("100.00"))

    def test_order_total_reconciliation_then_refund_uses_outstanding_net(self):
        self.update(payment_status=Order.PaymentStatus.PAID)
        self.edit_order_price(Decimal("35.50"))

        refund = self.record_refund()

        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(refund.amount, Decimal("35.50"))
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.REFUNDED)
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertEqual(
            sum(
                (txn.amount if txn.type == CustomerTransaction.Type.DEBIT else -txn.amount)
                for txn in CustomerTransaction.objects.filter(
                    order=self.order, is_order_settlement=True
                )
            ),
            Decimal("0.00"),
        )

    def test_inconsistent_account_balance_history_fails_closed_for_refund(self):
        self.update(payment_status=Order.PaymentStatus.PAID)
        self.edit_order_price(Decimal("35.50"))
        second_debit = CustomerTransaction.objects.get(
            order=self.order,
            type=CustomerTransaction.Type.DEBIT,
            amount=Decimal("10.00"),
        )
        CustomerTransaction.objects.filter(pk=second_debit.pk).update(
            balance_after=Decimal("74.50")
        )

        with self.assertRaises(ValidationError):
            self.record_refund()

        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(self.account.balance, Decimal("64.50"))
        self.assertFalse(OrderRefund.objects.filter(order=self.order).exists())

    def test_unsettled_wallet_order_cannot_be_refunded(self):
        self.order.payment_status = Order.PaymentStatus.PAID
        self.order.save(update_fields=["payment_status"])
        with self.assertRaises(ValidationError):
            self.record_refund()
        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertFalse(OrderRefund.objects.filter(order=self.order).exists())

    def test_status_update_cannot_claim_refund_without_refund_operation(self):
        with self.assertRaises(ValidationError):
            self.update(payment_status=Order.PaymentStatus.REFUNDED)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)

    def test_wallet_refund_failure_rolls_back_all_changes(self):
        self.update(payment_status=Order.PaymentStatus.PAID)
        initial_activity_count = ActivityLog.objects.filter(
            entity_type="order", entity_id=self.order.id
        ).count()
        original_credit = WalletService.record_refund_credit

        def credit_then_fail(**kwargs):
            original_credit(**kwargs)
            raise RuntimeError("refund credit failed")

        with patch.object(
            WalletService, "record_refund_credit", side_effect=credit_then_fail
        ):
            with self.assertRaisesRegex(RuntimeError, "refund credit failed"):
                self.record_refund()

        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(self.account.balance, Decimal("74.50"))
        self.assertEqual(CustomerTransaction.objects.filter(order=self.order).count(), 1)
        self.assertFalse(OrderRefund.objects.filter(order=self.order).exists())
        self.assertEqual(
            ActivityLog.objects.filter(entity_type="order", entity_id=self.order.id).count(),
            initial_activity_count,
        )

    def test_cancelling_paid_wallet_order_preserves_settlement_until_refunded(self):
        self.update(payment_status=Order.PaymentStatus.PAID)
        self.update(status=Order.Status.CANCELLED)
        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CANCELLED)
        self.assertEqual(self.account.balance, Decimal("74.50"))
        self.assertEqual(CustomerTransaction.objects.filter(order=self.order).count(), 1)

    def test_cancelled_wallet_order_cannot_start_a_new_settlement(self):
        self.update(status=Order.Status.CANCELLED)
        with self.assertRaises(ValidationError):
            self.update(payment_status=Order.PaymentStatus.PAID)
        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CANCELLED)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertFalse(CustomerTransaction.objects.filter(order=self.order).exists())

    def test_unclassified_order_ledger_is_rejected_without_recharging(self):
        self.account.balance = Decimal("105.00")
        self.account.save(update_fields=["balance"])
        CustomerTransaction.objects.create(
            account=self.account,
            order=self.order,
            type=CustomerTransaction.Type.CREDIT,
            amount=Decimal("5.00"),
            balance_after=Decimal("105.00"),
            description="Unclassified linked credit",
        )
        with self.assertRaises(ValidationError):
            self.update(payment_status=Order.PaymentStatus.PAID)
        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(self.account.balance, Decimal("105.00"))
        self.assertEqual(CustomerTransaction.objects.filter(order=self.order).count(), 1)

    def test_historically_flagged_order_debit_is_not_trusted_without_verification(self):
        self.account.balance = Decimal("90.00")
        self.account.save(update_fields=["balance"])
        CustomerTransaction.objects.create(
            account=self.account,
            order=self.order,
            type=CustomerTransaction.Type.DEBIT,
            amount=Decimal("10.00"),
            balance_after=Decimal("90.00"),
            # Migration 0016 may set this flag based on order/type alone.
            is_order_settlement=True,
            is_order_settlement_verified=False,
            description="Legacy order-linked debit",
        )

        with self.assertRaisesRegex(ValidationError, "unclassified"):
            self.update(payment_status=Order.PaymentStatus.PAID)

        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(self.account.balance, Decimal("90.00"))
        self.assertEqual(CustomerTransaction.objects.filter(order=self.order).count(), 1)

    def test_ordinary_order_linked_debit_is_not_settlement_evidence(self):
        debit = WalletService.debit(
            business=self.business,
            customer=self.customer,
            amount=Decimal("5.00"),
            order=self.order,
        )

        self.assertFalse(debit.is_order_settlement)
        self.assertFalse(debit.is_order_settlement_verified)
        with self.assertRaises(ValidationError):
            self.update(payment_status=Order.PaymentStatus.PAID)

    def test_debit_caller_cannot_supply_settlement_boolean(self):
        with self.assertRaises(TypeError):
            WalletService.debit(
                business=self.business,
                customer=self.customer,
                amount=Decimal("5.00"),
                order=self.order,
                order_settlement=True,
            )

    def test_authoritative_order_payment_creates_verified_settlement(self):
        self.update(payment_status=Order.PaymentStatus.PAID)
        debit = CustomerTransaction.objects.get(order=self.order)
        self.assertTrue(debit.is_order_settlement)
        self.assertTrue(debit.is_order_settlement_verified)

    def test_wallet_service_opens_new_accounts_from_a_verified_zero_baseline(self):
        customer = Customer.objects.create(
            business=self.business, name="New wallet customer", phone="12347"
        )

        account = WalletService.get_or_create_account(
            business=self.business,
            customer=customer,
        )

        self.assertEqual(account.balance, Decimal("0"))
        self.assertEqual(account.ledger_opening_balance, Decimal("0"))
        self.assertTrue(account.ledger_opening_balance_verified)

    def test_unverified_legacy_opening_balance_blocks_wallet_settlement(self):
        self.account.ledger_opening_balance_verified = False
        self.account.save(update_fields=["ledger_opening_balance_verified"])

        for operation in (WalletService.credit, WalletService.debit, WalletService.adjust):
            with self.subTest(operation=operation.__name__):
                with self.assertRaisesRegex(ValidationError, "opening balance is unverified"):
                    operation(
                        business=self.business,
                        customer=self.customer,
                        amount=Decimal("1.00"),
                    )

        with self.assertRaisesRegex(ValidationError, "opening balance is unverified"):
            self.update(payment_status=Order.PaymentStatus.PAID)

        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertFalse(CustomerTransaction.objects.filter(order=self.order).exists())

    def test_customer_account_model_defaults_opening_balance_to_unverified(self):
        customer = Customer.objects.create(
            business=self.business, name="Legacy account", phone="12348"
        )

        account = CustomerAccount.objects.create(
            business=self.business,
            customer=customer,
        )

        self.assertEqual(account.ledger_opening_balance, Decimal("0"))
        self.assertFalse(account.ledger_opening_balance_verified)

    def test_defaulted_legacy_balance_snapshot_blocks_wallet_settlement(self):
        self.account.balance = Decimal("90.00")
        self.account.save(update_fields=["balance"])
        CustomerTransaction.objects.create(
            account=self.account,
            type=CustomerTransaction.Type.DEBIT,
            amount=Decimal("10.00"),
            balance_after=Decimal("0.00"),
        )

        with self.assertRaisesRegex(ValidationError, "history is inconsistent"):
            self.update(payment_status=Order.PaymentStatus.PAID)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("90.00"))
        self.assertEqual(CustomerTransaction.objects.filter(order=self.order).count(), 0)

    def test_inconsistent_first_balance_snapshot_blocks_wallet_settlement(self):
        self.account.balance = Decimal("90.00")
        self.account.save(update_fields=["balance"])
        CustomerTransaction.objects.create(
            account=self.account,
            type=CustomerTransaction.Type.DEBIT,
            amount=Decimal("10.00"),
            balance_after=Decimal("91.00"),
        )

        with self.assertRaisesRegex(ValidationError, "history is inconsistent"):
            self.update(payment_status=Order.PaymentStatus.PAID)

    def test_dedicated_refund_credit_requires_exact_validated_settlement(self):
        self.update(payment_status=Order.PaymentStatus.PAID)
        refund = OrderRefund.objects.create(
            order=self.order,
            business=self.business,
            customer=self.customer,
            payment_method=Order.PaymentMethod.CUSTOMER_ACCOUNT,
            amount=Decimal("5.00"),
            reason="Amount mismatch regression",
            idempotency_key=uuid4(),
        )

        with self.assertRaisesRegex(ValidationError, "does not match the validated"):
            WalletService.record_refund_credit(
                business=self.business,
                refund=refund,
            )

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("74.50"))
        self.assertEqual(
            CustomerTransaction.objects.filter(
                order=self.order, type=CustomerTransaction.Type.DEBIT
            ).count(),
            1,
        )
        self.assertFalse(CustomerTransaction.objects.filter(
            order=self.order, type=CustomerTransaction.Type.CREDIT
        ).exists())

    def test_customer_account_payment_requires_customer_from_same_business(self):
        self.order.customer = None
        self.order.save(update_fields=["customer"])
        with self.assertRaises(ValidationError):
            self.update(payment_status=Order.PaymentStatus.PAID)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(self.account.balance, Decimal("100.00"))

    def test_customer_account_pending_method_can_be_selected_without_customer(self):
        self.order.customer = None
        self.order.payment_method = Order.PaymentMethod.CASH
        self.order.save(update_fields=["customer", "payment_method"])

        self.update(payment_method=Order.PaymentMethod.CUSTOMER_ACCOUNT)

        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_method, Order.PaymentMethod.CUSTOMER_ACCOUNT)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)
        self.assertFalse(CustomerTransaction.objects.filter(order=self.order).exists())

    def test_wallet_settlement_with_same_amount_creates_no_adjustment(self):
        self.update(payment_status=Order.PaymentStatus.PAID)
        self.edit_order_price(Decimal("25.50"))
        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.total_amount, Decimal("25.50"))
        self.assertEqual(self.account.balance, Decimal("74.50"))
        self.assertEqual(self.account.transactions.filter(type="debit").count(), 1)

    def test_wallet_settlement_increase_debits_only_difference_and_repeats_idempotently(self):
        self.update(payment_status=Order.PaymentStatus.PAID)
        self.edit_order_price(Decimal("35.50"))
        self.edit_order_price(Decimal("35.50"))
        self.order.refresh_from_db()
        self.account.refresh_from_db()
        debits = CustomerTransaction.objects.filter(
            order=self.order, type=CustomerTransaction.Type.DEBIT,
            is_order_settlement=True,
        )
        self.assertEqual(self.order.total_amount, Decimal("35.50"))
        self.assertEqual(self.account.balance, Decimal("64.50"))
        self.assertEqual(debits.count(), 2)
        self.assertEqual(
            sorted(debits.values_list("amount", flat=True)),
            [Decimal("10.00"), Decimal("25.50")],
        )

    def test_wallet_settlement_decrease_is_rejected_without_refund_operation(self):
        self.update(payment_status=Order.PaymentStatus.PAID)
        with self.assertRaises(ValidationError):
            self.edit_order_price(Decimal("15.50"))
        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.total_amount, Decimal("25.50"))
        self.assertEqual(self.account.balance, Decimal("74.50"))
        self.assertEqual(
            CustomerTransaction.objects.filter(
                order=self.order, type=CustomerTransaction.Type.CREDIT,
                is_order_settlement=True,
            ).count(),
            0,
        )

    def test_payment_state_corrections_cannot_credit_settled_wallet(self):
        self.update(payment_status=Order.PaymentStatus.PAID)
        for payment_status in (
            Order.PaymentStatus.PENDING,
            Order.PaymentStatus.UNPAID,
            Order.PaymentStatus.FAILED,
        ):
            with self.subTest(payment_status=payment_status):
                with self.assertRaises(ValidationError):
                    self.update(payment_status=payment_status)
                self.order.refresh_from_db()
                self.account.refresh_from_db()
                self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
                self.assertEqual(self.account.balance, Decimal("74.50"))
                self.assertFalse(CustomerTransaction.objects.filter(
                    order=self.order, type=CustomerTransaction.Type.CREDIT
                ).exists())

    def test_method_switch_cannot_credit_settled_wallet(self):
        self.update(payment_status=Order.PaymentStatus.PAID)
        with self.assertRaises(ValidationError):
            self.update(
                payment_method=Order.PaymentMethod.CARD,
                payment_status=Order.PaymentStatus.UNPAID,
            )
        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.payment_method, Order.PaymentMethod.CUSTOMER_ACCOUNT)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(self.account.balance, Decimal("74.50"))
        self.assertFalse(CustomerTransaction.objects.filter(
            order=self.order, type=CustomerTransaction.Type.CREDIT
        ).exists())

    def test_wallet_adjustment_failure_rolls_back_edit_balance_ledger_and_activity(self):
        OrderItem.objects.create(
            order=self.order,
            menu_item=self.menu_item,
            menu_item_name=self.menu_item.name,
            quantity=1,
            unit_price=Decimal("25.50"),
            total_price=Decimal("25.50"),
        )
        self.update(payment_status=Order.PaymentStatus.PAID)
        initial_activity_count = ActivityLog.objects.filter(
            entity_type="order", entity_id=self.order.id
        ).count()
        original_settle = WalletService.settle_order

        def settle_then_fail(**kwargs):
            original_settle(**kwargs)
            raise RuntimeError("wallet adjustment failed after debit")

        self.menu_item.price = Decimal("35.50")
        self.menu_item.save(update_fields=["price"])
        with patch.object(WalletService, "settle_order", side_effect=settle_then_fail):
            with self.assertRaisesRegex(RuntimeError, "adjustment failed"):
                OrderService.update_order(
                    business=self.business,
                    order_id=self.order.id,
                    validated_data={
                        "items": [{"menu_item_id": self.menu_item.id, "quantity": 1}]
                    },
                )

        self.order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.order.total_amount, Decimal("25.50"))
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(self.order.items.get().unit_price, Decimal("25.50"))
        self.assertEqual(self.account.balance, Decimal("74.50"))
        self.assertEqual(
            CustomerTransaction.objects.filter(
                order=self.order, is_order_settlement=True
            ).count(),
            1,
        )
        self.assertEqual(
            ActivityLog.objects.filter(
                entity_type="order", entity_id=self.order.id
            ).count(),
            initial_activity_count,
        )

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
            self.update(payment_status=Order.PaymentStatus.PAID)
        self.account.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("100.00"))
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertFalse(CustomerTransaction.objects.filter(order=self.order).exists())

    def test_paid_wallet_order_with_matching_debit_validates_without_recharging(self):
        self.update(payment_status=Order.PaymentStatus.PAID)
        self.update(payment_status=Order.PaymentStatus.PAID)
        self.complete_order()
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("74.50"))
        self.assertEqual(CustomerTransaction.objects.filter(order=self.order, type="debit").count(), 1)

    def test_paid_wallet_order_reconciles_existing_settlement_to_current_amount(self):
        self.account.balance = Decimal("90.00")
        self.account.save(update_fields=["balance"])
        self.order.payment_status = Order.PaymentStatus.PAID
        self.order.save(update_fields=["payment_status"])
        CustomerTransaction.objects.create(
            account=self.account,
            order=self.order,
            type=CustomerTransaction.Type.DEBIT,
            amount=Decimal("10.00"),
            balance_after=Decimal("90.00"),
            is_order_settlement=True,
            is_order_settlement_verified=True,
        )
        self.update(payment_status=Order.PaymentStatus.PAID)
        self.account.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("74.50"))
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(CustomerTransaction.objects.filter(
            order=self.order, type=CustomerTransaction.Type.DEBIT,
            is_order_settlement=True,
        ).count(), 2)

    def test_order_ledger_for_another_account_is_rejected_without_charge(self):
        other_customer = Customer.objects.create(
            business=self.business, name="Other wallet owner", phone="12346"
        )
        other_account = CustomerAccount.objects.create(
            business=self.business,
            customer=other_customer,
            balance=Decimal("50.00"),
            ledger_opening_balance=Decimal("50.00"),
            ledger_opening_balance_verified=True,
        )
        self.order.payment_status = Order.PaymentStatus.PAID
        self.order.save(update_fields=["payment_status"])
        CustomerTransaction.objects.create(
            account=other_account,
            order=self.order,
            type=CustomerTransaction.Type.DEBIT,
            amount=Decimal("10.00"),
            balance_after=Decimal("40.00"),
            is_order_settlement=True,
        )
        with self.assertRaises(ValidationError):
            self.update(payment_status=Order.PaymentStatus.PAID)
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
            order.status = Order.Status.READY
            order.save(update_fields=("status",))
            OrderService.update_status(
                business=self.business,
                order_id=order.id,
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

    def test_refunded_non_wallet_order_cannot_be_deleted(self):
        refunded_order = Order.objects.create(
            business=self.business,
            order_type=Order.OrderType.TAKEAWAY,
            payment_method=Order.PaymentMethod.CARD,
            payment_status=Order.PaymentStatus.REFUNDED,
        )
        with self.assertRaises(ValidationError):
            OrderService.delete_order(refunded_order)
        self.assertTrue(Order.objects.filter(pk=refunded_order.pk).exists())

    def test_unknown_payment_state_fails_closed_on_deletion(self):
        order = Order.objects.create(
            business=self.business,
            order_type=Order.OrderType.TAKEAWAY,
            payment_status="unknown_legacy_state",
        )
        with self.assertRaises(ValidationError):
            OrderService.delete_order(order)
        self.assertTrue(Order.objects.filter(pk=order.pk).exists())

    def test_cancelled_unpaid_and_failed_orders_without_history_can_be_deleted(self):
        cases = (
            (Order.Status.CANCELLED, Order.PaymentStatus.UNPAID),
            (Order.Status.FAILED, Order.PaymentStatus.FAILED),
        )
        for status, payment_status in cases:
            with self.subTest(status=status, payment_status=payment_status):
                order = Order.objects.create(
                    business=self.business,
                    order_type=Order.OrderType.TAKEAWAY,
                    status=status,
                    payment_status=payment_status,
                )
                OrderService.delete_order(order)
                self.assertFalse(Order.objects.filter(pk=order.pk).exists())

    def test_order_with_non_debit_wallet_history_cannot_be_deleted(self):
        self.account.balance = Decimal("105.00")
        self.account.save(update_fields=["balance"])
        transaction = CustomerTransaction.objects.create(
            account=self.account,
            order=self.order,
            type=CustomerTransaction.Type.CREDIT,
            amount=Decimal("5.00"),
            balance_after=Decimal("105.00"),
            description="Order-linked credit",
        )
        with self.assertRaises(ValidationError):
            OrderService.delete_order(self.order)
        transaction.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(transaction.order_id, self.order.id)
        self.assertEqual(self.account.balance, Decimal("105.00"))

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
        self.account.ledger_opening_balance = Decimal("5.00")
        self.account.save(update_fields=["balance", "ledger_opening_balance"])
        self.update(payment_status=Order.PaymentStatus.PAID)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("-20.50"))


class WalletDebitMigrationTests(TestCase):
    def test_duplicate_check_fails_with_order_reference_without_mutating_data(self):
        query = Mock()
        grouped_query = (
            query.using.return_value.filter.return_value.values.return_value
            .annotate.return_value.filter.return_value
        )
        ordered_query = grouped_query.order_by.return_value
        ordered_query.first.return_value = {"order_id": 812}
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
        grouped_query.order_by.assert_called_once_with("order_id")
        query.delete.assert_not_called()


class WalletRefundMigrationTests(TestCase):
    def test_refund_migration_reverse_preserves_existing_permission_links(self):
        business = Business.objects.create(name="Migration Permission Business")
        role = Role.objects.create(business=business, name="Owner", code="OWNER")
        permission = Permission.objects.get(code="payments.manage")
        assignment = RolePermission.objects.create(role=role, permission=permission)

        migration = import_module("products.migrations.0017_order_refund_audit")
        migration.revoke_payment_management(
            apps=SimpleNamespace(),
            schema_editor=SimpleNamespace(connection=SimpleNamespace(alias="default")),
        )

        self.assertTrue(Permission.objects.filter(pk=permission.pk).exists())
        self.assertTrue(RolePermission.objects.filter(pk=assignment.pk).exists())
