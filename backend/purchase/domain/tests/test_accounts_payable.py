from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase

from purchase.domain.entities.accounts_payable import AccountsPayable
from purchase.domain.enums.accounts_payable_status import AccountsPayableStatus


class AccountsPayableDomainTests(SimpleTestCase):
    def payable(self, **overrides):
        values = {
            "id": None,
            "business_id": 1,
            "supplier_id": 2,
            "source_invoice_id": 3,
            "amount": Decimal("125.50"),
            "due_date": date(2026, 11, 15),
        }
        values.update(overrides)
        return AccountsPayable(**values)

    def test_positive_amount_is_accepted_and_new_payable_is_open(self):
        payable = self.payable()
        self.assertEqual(payable.amount, Decimal("125.50"))
        self.assertEqual(payable.status, AccountsPayableStatus.OPEN)

    def test_zero_amount_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            self.payable(amount=Decimal("0"))

    def test_negative_amount_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            self.payable(amount=Decimal("-1"))

    def test_financial_snapshot_fields_are_stored_as_values(self):
        payable = self.payable()
        self.assertEqual(payable.business_id, 1)
        self.assertEqual(payable.supplier_id, 2)
        self.assertEqual(payable.source_invoice_id, 3)
        self.assertEqual(payable.due_date, date(2026, 11, 15))
        self.assertIsNone(payable.posted_at)
        self.assertIsNone(payable.posted_by_id)
        self.assertIsNone(payable.cancelled_at)
        self.assertIsNone(payable.cancelled_by_id)
        self.assertEqual(payable.cancellation_reason, "")

    def test_new_payable_cannot_start_in_a_future_status(self):
        with self.assertRaisesRegex(ValueError, "start as open"):
            self.payable(status=AccountsPayableStatus.PAID)
