from datetime import date
from decimal import Decimal
from unittest import TestCase

from purchase.domain.entities.supplier_payment import SupplierPayment
from purchase.domain.enums.payment_method import PaymentMethod


class SupplierPaymentDomainTests(TestCase):
    def payment(self, **overrides):
        values = {
            "id": None,
            "business_id": 1,
            "supplier_id": 1,
            "amount": Decimal("100.00"),
            "payment_date": date(2026, 9, 19),
            "method": PaymentMethod.BANK_TRANSFER,
        }
        values.update(overrides)
        return SupplierPayment(**values)

    def test_valid_payment_is_independent_from_invoice(self):
        payment = self.payment()
        self.assertEqual(payment.amount, Decimal("100.00"))
        self.assertEqual(payment.method, PaymentMethod.BANK_TRANSFER)

    def test_zero_and_negative_amounts_are_rejected(self):
        with self.assertRaises(ValueError):
            self.payment(amount=Decimal("0"))
        with self.assertRaises(ValueError):
            self.payment(amount=Decimal("-1.00"))

    def test_invalid_method_is_rejected(self):
        with self.assertRaises(ValueError):
            self.payment(method="bitcoin")

    def test_all_payment_methods_are_accepted(self):
        for method in PaymentMethod:
            with self.subTest(method=method):
                self.assertEqual(self.payment(method=method).method, method)
