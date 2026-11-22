from decimal import Decimal
from uuid import uuid4

from django.db import connection, transaction
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from accounts.models import Business
from products.models import Customer, Order, OrderRefund
from products.infrastructure.django.order_refund_read_repository import (
    DjangoOrderRefundReadRepository,
)


class DjangoOrderRefundReadRepositoryTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Refund Read Business")
        self.other_business = Business.objects.create(name="Other Refund Read Business")
        self.customer = Customer.objects.create(
            business=self.business,
            name="Refund Read Customer",
            phone="88001",
        )
        self.order = Order.objects.create(
            business=self.business,
            customer=self.customer,
            order_type=Order.OrderType.TAKEAWAY,
            payment_method=Order.PaymentMethod.CUSTOMER_ACCOUNT,
            payment_status=Order.PaymentStatus.REFUNDED,
            total_amount=Decimal("18.50"),
        )
        self.refund = OrderRefund.objects.create(
            order=self.order,
            business=self.business,
            customer=self.customer,
            payment_method=Order.PaymentMethod.CUSTOMER_ACCOUNT,
            amount=Decimal("18.50"),
            reason="Customer requested return",
            idempotency_key=uuid4(),
        )
        self.repository = DjangoOrderRefundReadRepository()

    def test_returns_tenant_scoped_order_and_materialized_refund_list(self):
        with transaction.atomic():
            with CaptureQueriesContext(connection) as queries:
                order, refunds = self.repository.get_recovery_state_for_business(
                    self.business.pk, self.order.pk,
                )

        self.assertEqual(order.pk, self.order.pk)
        self.assertEqual([refund.pk for refund in refunds], [self.refund.pk])
        self.assertIsInstance(refunds, list)
        self.assertFalse(any("SELECT" in str(type(value)) for value in refunds))
        if connection.vendor == "postgresql":
            self.assertTrue(
                any("FOR UPDATE" in query["sql"].upper() for query in queries),
                "The recovery lookup must retain its Order row lock.",
            )

    def test_hides_order_and_refunds_from_another_business(self):
        order, refunds = self.repository.get_recovery_state_for_business(
            self.other_business.pk, self.order.pk,
        )

        self.assertIsNone(order)
        self.assertEqual(refunds, [])

    def test_materializes_all_matching_refunds_for_duplicate_detection(self):
        second = OrderRefund.objects.create(
            order=self.order,
            business=self.business,
            customer=self.customer,
            payment_method=Order.PaymentMethod.CUSTOMER_ACCOUNT,
            amount=Decimal("18.50"),
            reason="Duplicate fixture",
            idempotency_key=uuid4(),
        )

        order, refunds = self.repository.get_recovery_state_for_business(
            self.business.pk, self.order.pk,
        )

        self.assertEqual(order.pk, self.order.pk)
        self.assertEqual([refund.pk for refund in refunds], sorted([self.refund.pk, second.pk]))
