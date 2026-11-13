from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4


from django.db import DatabaseError, connection
from django.test import TestCase, TransactionTestCase
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Permission, Role, RolePermission, User
from core.enums import PermissionCode
from products.models import (
    Customer, CustomerAccount, Order, OrderPaymentEvent, OrderRefund, OrderStatusHistory,
)
from products.services.order_service import OrderService


class OrderPaymentEventServiceTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Payment Audit Business")
        self.actor = User.objects.create_user(
            email="payment-audit@example.test",
            password="test-password",
            name="Payment Audit Actor",
            number="88001",
        )
        self.customer = Customer.objects.create(
            business=self.business, name="Audit Customer", phone="88002",
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
            payment_method=Order.PaymentMethod.CASH,
            payment_status=Order.PaymentStatus.PENDING,
            subtotal=Decimal("25.50"),
            total_amount=Decimal("25.50"),
        )

    def test_status_update_records_payment_before_and_after(self):
        OrderService.update_status(
            business=self.business,
            order_id=self.order.pk,
            payment_status=Order.PaymentStatus.FAILED,
            payment_method=Order.PaymentMethod.CARD,
            user=self.actor,
        )
        event = OrderPaymentEvent.objects.get(order_id_snapshot=self.order.pk)
        self.assertEqual(event.from_payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(event.to_payment_status, Order.PaymentStatus.FAILED)
        self.assertEqual(event.from_payment_method, Order.PaymentMethod.CASH)
        self.assertEqual(event.to_payment_method, Order.PaymentMethod.CARD)
        self.assertEqual(event.actor_id, self.actor.pk)

    def test_wallet_settlement_records_payment_event(self):
        self.order.payment_method = Order.PaymentMethod.CUSTOMER_ACCOUNT
        self.order.save(update_fields=["payment_method"])
        OrderService.pay_order(order=self.order, business=self.business, user=self.actor)
        event = OrderPaymentEvent.objects.get(order_id_snapshot=self.order.pk)
        self.assertEqual(event.event_type, OrderPaymentEvent.EventType.PAYMENT_SETTLED)
        self.assertEqual(event.from_payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(event.to_payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(event.actor_id, self.actor.pk)

    def test_order_total_edit_records_before_and_after(self):
        OrderService.update_order(
            business=self.business,
            order_id=self.order.pk,
            validated_data={"discount": Decimal("2.00")},
            user=self.actor,
        )
        event = OrderPaymentEvent.objects.get(order_id_snapshot=self.order.pk)
        self.assertEqual(event.event_type, OrderPaymentEvent.EventType.ORDER_TOTAL_CHANGED)
        self.assertEqual(event.from_total_amount, Decimal("25.50"))
        self.assertEqual(event.to_total_amount, Decimal("23.50"))


    def test_wallet_settlement_failure_rolls_back_order_and_payment_event(self):
        self.order.payment_method = Order.PaymentMethod.CUSTOMER_ACCOUNT
        self.order.save(update_fields=["payment_method"])

        with patch.object(
            OrderService,
            "_reconcile_order_settlement",
            side_effect=RuntimeError("simulated wallet settlement failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "simulated wallet settlement failure"):
                OrderService.pay_order(
                    order=self.order, business=self.business, user=self.actor,
                )

        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)
        self.assertFalse(
            OrderPaymentEvent.objects.filter(order_id_snapshot=self.order.pk).exists()
        )

    def test_payment_event_write_failure_rolls_back_order_mutation(self):
        self.order.payment_method = Order.PaymentMethod.CUSTOMER_ACCOUNT
        self.order.save(update_fields=["payment_method"])

        with patch.object(
            OrderService,
            "_record_payment_event",
            side_effect=DatabaseError("simulated audit write failure"),
        ):
            with self.assertRaisesRegex(DatabaseError, "simulated audit write failure"):
                OrderService.pay_order(
                    order=self.order, business=self.business, user=self.actor,
                )

        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)
        self.assertFalse(
            OrderPaymentEvent.objects.filter(order_id_snapshot=self.order.pk).exists()
        )

    def test_refund_event_contains_actor_amount_reason_and_reference(self):
        self.order.payment_method = Order.PaymentMethod.CUSTOMER_ACCOUNT
        self.order.payment_status = Order.PaymentStatus.PAID
        self.order.save(update_fields=["payment_method", "payment_status"])
        key = uuid4()

        with (
            patch.object(
                OrderService, "_validated_order_settlement",
                return_value=(Decimal("25.50"), []),
            ),
            patch.object(OrderService, "_reconcile_order_settlement"),
            patch("products.services.order_service.OrderInventoryService.release_remaining"),
            patch("products.services.order_service.ActivityLogService.record"),
        ):
            refund = OrderService.refund_order(
                business=self.business,
                order_id=self.order.pk,
                user=self.actor,
                idempotency_key=key,
                reason="Customer request",
                reference="BANK-REF-42",
            )

        event = OrderPaymentEvent.objects.get(
            business=self.business,
            order_id_snapshot=self.order.pk,
            event_type=OrderPaymentEvent.EventType.PAYMENT_REFUNDED,
        )
        self.assertEqual(refund.amount, Decimal("25.50"))
        self.assertEqual(event.actor_id, self.actor.pk)
        self.assertEqual(event.metadata["refund_amount"], "25.50")
        self.assertEqual(event.metadata["reason"], "Customer request")
        self.assertEqual(event.metadata["reference"], "BANK-REF-42")
        self.assertEqual(event.metadata["refund_id"], refund.pk)

    def test_refund_followup_failure_rolls_back_refund_order_and_audit_event(self):
        self.order.payment_method = Order.PaymentMethod.CUSTOMER_ACCOUNT
        self.order.payment_status = Order.PaymentStatus.PAID
        self.order.save(update_fields=["payment_method", "payment_status"])
        key = uuid4()

        with (
            patch.object(
                OrderService, "_validated_order_settlement",
                return_value=(Decimal("25.50"), []),
            ),
            patch.object(OrderService, "_reconcile_order_settlement"),
            patch("products.services.order_service.OrderInventoryService.release_remaining"),
            patch(
                "products.services.order_service.ActivityLogService.record",
                side_effect=RuntimeError("simulated post-audit activity failure"),
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "simulated post-audit activity failure"):
                OrderService.refund_order(
                    business=self.business,
                    order_id=self.order.pk,
                    user=self.actor,
                    idempotency_key=key,
                    reason="Customer request",
                    reference="BANK-REF-43",
                )

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertFalse(OrderRefund.objects.filter(idempotency_key=key).exists())
        self.assertFalse(
            OrderPaymentEvent.objects.filter(order_id_snapshot=self.order.pk).exists()
        )
        self.assertFalse(
            OrderStatusHistory.objects.filter(order_id_snapshot=self.order.pk).exists()
        )


class OrderPaymentEventApiTests(APITestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Payment API Business")
        self.other_business = Business.objects.create(name="Other Payment API Business")
        self.user = User.objects.create_user(
            email="payment-api@example.test",
            password="test-password",
            name="Payment API Actor",
            number="88011",
        )
        self.payment_permission, _ = Permission.objects.get_or_create(
            code=PermissionCode.PAYMENTS_MANAGE.value,
            defaults={"name": PermissionCode.PAYMENTS_MANAGE.label},
        )
        self.role = self._create_financial_membership(self.business, "OWNER")
        self._create_financial_membership(self.other_business, "OWNER")
        self.order = Order.objects.create(
            business=self.business,
            order_type=Order.OrderType.TAKEAWAY,
            payment_method=Order.PaymentMethod.CASH,
            payment_status=Order.PaymentStatus.PENDING,
            subtotal=Decimal("40.00"),
            total_amount=Decimal("40.00"),
        )
        self.event = OrderPaymentEvent.objects.create(
            business=self.business,
            order_id_snapshot=self.order.pk,
            event_type=OrderPaymentEvent.EventType.PAYMENT_UPDATED,
            from_payment_status=Order.PaymentStatus.PENDING,
            to_payment_status=Order.PaymentStatus.FAILED,
            metadata={"audit_marker": "business-a-only"},
            actor=self.user,
        )
        self.client.force_authenticate(self.user)
        self.client.defaults["HTTP_X_BUSINESS_ID"] = str(self.business.pk)

    def _create_financial_membership(self, business, role_code):
        role = Role.objects.create(
            business=business,
            name=f"{role_code} Payment Role",
            code=role_code,
        )
        Membership.objects.create(
            user=self.user,
            business=business,
            role=role,
            is_active=True,
        )
        RolePermission.objects.get_or_create(
            role=role,
            permission=self.payment_permission,
        )
        return role

    def test_payment_event_endpoint_returns_scoped_event_and_actor(self):
        response = self.client.get(
            f"/api/products/orders/{self.order.pk}/payment-events/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["order_id"], self.order.pk)
        self.assertEqual(len(response.data["events"]), 1)
        self.assertEqual(response.data["events"][0]["id"], self.event.pk)
        self.assertEqual(response.data["events"][0]["actor"]["id"], self.user.pk)
        self.assertEqual(
            response.data["events"][0]["metadata"]["audit_marker"],
            "business-a-only",
        )
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_payment_event_endpoint_does_not_disclose_foreign_business_order(self):
        self.client.defaults["HTTP_X_BUSINESS_ID"] = str(self.other_business.pk)

        response = self.client.get(
            f"/api/products/orders/{self.order.pk}/payment-events/"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNotIn("business-a-only", str(response.data))
        self.assertNotIn(str(self.event.pk), str(response.data))

    def test_payment_event_endpoint_requires_financial_permission(self):
        RolePermission.objects.filter(
            role=self.role,
            permission=self.payment_permission,
        ).delete()

        response = self.client.get(
            f"/api/products/orders/{self.order.pk}/payment-events/"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_payment_event_endpoint_rejects_nonfinancial_role_with_permission(self):
        # A granted permission must not bypass the financial-role allowlist.
        self.role.code = "WAITER"
        self.role.save(update_fields=["code"])

        response = self.client.get(
            f"/api/products/orders/{self.order.pk}/payment-events/"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class OrderPaymentEventDatabaseImmutabilityTests(TransactionTestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Payment Event Guard Business")
        self.event = OrderPaymentEvent.objects.create(
            business=self.business,
            order_id_snapshot=1,
            event_type=OrderPaymentEvent.EventType.PAYMENT_UPDATED,
            from_payment_status=Order.PaymentStatus.PENDING,
            to_payment_status=Order.PaymentStatus.FAILED,
        )

    def test_model_rejects_instance_mutation(self):
        self.event.metadata = {"tampered": True}
        with self.assertRaises(Exception):
            self.event.save()

    def test_database_rejects_queryset_update_and_delete(self):
        if connection.vendor != "postgresql":
            self.skipTest("Database trigger is PostgreSQL-specific")
        with self.assertRaises(DatabaseError):
            OrderPaymentEvent.objects.filter(pk=self.event.pk).update(metadata={"tampered": True})
        self.event.refresh_from_db()
        with self.assertRaises(DatabaseError):
            OrderPaymentEvent.objects.filter(pk=self.event.pk).delete()
        self.assertTrue(OrderPaymentEvent.objects.filter(pk=self.event.pk).exists())
