from decimal import Decimal
from uuid import uuid4

from django.db import DatabaseError, connection
from django.test import TestCase, TransactionTestCase

from accounts.models import Business
from products.models import (
    Customer, CustomerAccount, Order, OrderPaymentEvent,
)
from products.services.order_service import OrderService
from accounts.models import User


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
