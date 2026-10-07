from datetime import datetime, timezone
from decimal import Decimal

from django.test import SimpleTestCase

from purchase.domain.entities.accounts_payable import AccountsPayable
from purchase.domain.entities.payment_allocation import PaymentAllocation
from purchase.domain.enums.accounts_payable_status import AccountsPayableStatus
from purchase.domain.services.accounts_payable_payment_state import AccountsPayablePaymentStatePolicy


class PaymentAllocationDomainTests(SimpleTestCase):
    def allocation(self, **overrides):
        values = {
            "id": None,
            "business_id": 1,
            "accounts_payable_id": 2,
            "supplier_payment_id": 3,
            "amount": Decimal("25.00"),
            "allocated_at": datetime(2026, 10, 7, tzinfo=timezone.utc),
        }
        values.update(overrides)
        return PaymentAllocation(**values)

    def payable(self, **overrides):
        values = {
            "id": 2,
            "business_id": 1,
            "supplier_id": 3,
            "source_invoice_id": 4,
            "amount": Decimal("100.00"),
        }
        values.update(overrides)
        return AccountsPayable(**values)

    def test_positive_decimal_allocation_is_valid(self):
        self.assertEqual(self.allocation().amount, Decimal("25.00"))

    def test_zero_and_negative_allocation_are_rejected(self):
        for value in (Decimal("0"), Decimal("-1")):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "greater than zero"):
                self.allocation(amount=value)

    def test_non_decimal_allocation_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Decimal"):
            self.allocation(amount=25.0)

    def test_payment_state_derives_open_partial_and_paid_from_totals(self):
        payable = self.payable()
        cases = (
            (Decimal("0"), AccountsPayableStatus.OPEN, Decimal("100.00"), True),
            (Decimal("40"), AccountsPayableStatus.PARTIALLY_PAID, Decimal("60.00"), True),
            (Decimal("100"), AccountsPayableStatus.PAID, Decimal("0.00"), False),
        )
        for allocated, status, outstanding, eligible in cases:
            with self.subTest(allocated=allocated):
                state = AccountsPayablePaymentStatePolicy.calculate(payable, allocated)
                self.assertEqual(state.status, status)
                self.assertEqual(state.allocated_amount, allocated.quantize(Decimal("0.01")))
                self.assertEqual(state.outstanding_amount, outstanding)
                self.assertEqual(state.eligible, eligible)

    def test_allocated_amount_cannot_exceed_payable_total(self):
        with self.assertRaisesRegex(ValueError, "between zero"):
            AccountsPayablePaymentStatePolicy.calculate(self.payable(), Decimal("100.01"))

    def test_cancelled_payable_remains_cancelled_and_ineligible(self):
        state = AccountsPayablePaymentStatePolicy.calculate(
            self.payable(status=AccountsPayableStatus.CANCELLED), Decimal("0"),
        )
        self.assertEqual(state.status, AccountsPayableStatus.CANCELLED)
        self.assertFalse(state.eligible)
