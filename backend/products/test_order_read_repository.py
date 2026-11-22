from decimal import Decimal

from django.test import TestCase

from accounts.models import Business
from products.infrastructure.django.order_read_repository import DjangoOrderReadRepository
from products.models import Order


class DjangoOrderReadRepositoryTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Order Read Business")
        self.other_business = Business.objects.create(name="Other Order Read Business")
        self.repository = DjangoOrderReadRepository()

    def create_order(self, business=None, **overrides):
        values = {
            "business": business or self.business,
            "order_type": Order.OrderType.DINE_IN,
            "status": Order.Status.PENDING,
            "payment_method": Order.PaymentMethod.CASH,
            "payment_status": Order.PaymentStatus.PENDING,
            "total_amount": Decimal("10.00"),
        }
        values.update(overrides)
        return Order.objects.create(**values)

    def test_list_is_tenant_scoped_and_selects_customer(self):
        own = self.create_order()
        foreign = self.create_order(business=self.other_business)

        rows = self.repository.list_for_business(self.business.pk, {})

        self.assertEqual(list(rows.values_list("pk", flat=True)), [own.pk])
        self.assertIn("customer", rows.query.select_related)

    def test_list_preserves_status_payment_and_amount_filters(self):
        matching = self.create_order(
            status=Order.Status.CONFIRMED,
            payment_status=Order.PaymentStatus.PAID,
            payment_method=Order.PaymentMethod.CARD,
            total_amount=Decimal("25.00"),
        )
        self.create_order(total_amount=Decimal("5.00"))
        self.create_order(
            status=Order.Status.CONFIRMED,
            payment_status=Order.PaymentStatus.PENDING,
            payment_method=Order.PaymentMethod.CARD,
            total_amount=Decimal("25.00"),
        )

        rows = self.repository.list_for_business(
            self.business.pk,
            {
                "status": Order.Status.CONFIRMED,
                "payment_status": Order.PaymentStatus.PAID,
                "payment_method": Order.PaymentMethod.CARD,
                "min_total": "20",
                "max_total": "30",
            },
        )

        self.assertEqual(list(rows.values_list("pk", flat=True)), [matching.pk])

    def test_ordering_uses_id_as_deterministic_tie_breaker(self):
        first = self.create_order(total_amount=Decimal("10.00"))
        second = self.create_order(total_amount=Decimal("10.00"))

        ascending = self.repository.list_for_business(
            self.business.pk, {"ordering": "total_amount"}
        )
        descending = self.repository.list_for_business(
            self.business.pk, {"ordering": "-total_amount"}
        )

        self.assertEqual(
            list(ascending.values_list("pk", flat=True)),
            [first.pk, second.pk],
        )
        self.assertEqual(
            list(descending.values_list("pk", flat=True)),
            [second.pk, first.pk],
        )

    def test_invalid_ordering_falls_back_to_created_at_and_id_descending(self):
        first = self.create_order()
        second = self.create_order()

        rows = self.repository.list_for_business(
            self.business.pk, {"ordering": "customer__name"}
        )

        self.assertEqual(list(rows.values_list("pk", flat=True)), [second.pk, first.pk])

    def test_detail_lookup_is_tenant_scoped(self):
        own = self.create_order()
        foreign = self.create_order(business=self.other_business)

        self.assertEqual(
            self.repository.get_for_business(self.business.pk, own.pk).pk,
            own.pk,
        )
        self.assertIsNone(
            self.repository.get_for_business(self.business.pk, foreign.pk)
        )
