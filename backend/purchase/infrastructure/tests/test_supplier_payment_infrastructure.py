from datetime import date
from decimal import Decimal

from django.test import TestCase

from accounts.models import Business
from purchase.domain.entities.supplier_payment import SupplierPayment
from purchase.domain.enums.payment_method import PaymentMethod
from purchase.infrastructure.persistence.django.repositories.supplier_payment_repository import (
    DjangoSupplierPaymentRepository,
)
from purchase.models import Supplier, SupplierPayment as DjangoSupplierPayment


class SupplierPaymentInfrastructureTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Payment Business")
        self.other_business = Business.objects.create(name="Other Payment Business")
        self.supplier = Supplier.objects.create(
            business=self.business,
            name="Supplier",
        )
        self.other_supplier = Supplier.objects.create(
            business=self.other_business,
            name="Other Supplier",
        )
        self.repository = DjangoSupplierPaymentRepository()

    def payment(self, **overrides):
        values = {
            "id": None,
            "business_id": self.business.id,
            "supplier_id": self.supplier.id,
            "amount": Decimal("100.00"),
            "payment_date": date(2026, 9, 19),
            "method": PaymentMethod.CASH,
        }
        values.update(overrides)
        return SupplierPayment(**values)

    def test_create_and_get_are_business_scoped(self):
        saved = self.repository.save(self.payment())
        self.assertEqual(
            self.repository.get_by_id_for_business(saved.id, self.business.id).id,
            saved.id,
        )
        self.assertIsNone(
            self.repository.get_by_id_for_business(saved.id, self.other_business.id)
        )

    def test_list_is_business_scoped_and_payment_has_no_invoice(self):
        saved = self.repository.save(self.payment())
        other = DjangoSupplierPayment.objects.create(
            business=self.other_business,
            supplier=self.other_supplier,
            amount=Decimal("50.00"),
            payment_date=date(2026, 9, 19),
            method=PaymentMethod.CARD.value,
        )
        listed = self.repository.list(self.business.id)
        self.assertEqual([payment.id for payment in listed], [saved.id])
        self.assertNotIn(other.id, [payment.id for payment in listed])
        self.assertIsNone(DjangoSupplierPayment.objects.get(id=saved.id).invoice_id)

    def test_cross_business_supplier_is_rejected(self):
        with self.assertRaises(ValueError):
            self.repository.save(self.payment(supplier_id=self.other_supplier.id))

    def test_existing_supplier_payment_cannot_be_updated(self):
        saved = self.repository.save(self.payment())
        with self.assertRaisesRegex(ValueError, "immutable"):
            self.repository.save(self.payment(id=saved.id, amount=Decimal("1.00")))
