from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase

from purchase.domain.entities.accounts_payable import AccountsPayable
from purchase.domain.enums.accounts_payable_payment_eligibility_reason import (
    AccountsPayablePaymentEligibilityReason,
)
from purchase.domain.enums.accounts_payable_status import AccountsPayableStatus
from purchase.domain.services.accounts_payable_payment_eligibility import (
    AccountsPayablePaymentEligibilityPolicy,
)


class AccountsPayablePaymentEligibilityTests(SimpleTestCase):
    def payable(self, status):
        return AccountsPayable(
            id=8,
            business_id=1,
            supplier_id=2,
            source_invoice_id=3,
            amount=Decimal("12500000.00"),
            due_date=date(2026, 11, 15),
            status=status,
        )

    def test_open_is_eligible(self):
        result = AccountsPayablePaymentEligibilityPolicy.evaluate(
            self.payable(AccountsPayableStatus.OPEN),
        )
        self.assertTrue(result.eligible)
        self.assertIsNone(result.reason)

    def test_partially_paid_is_eligible(self):
        result = AccountsPayablePaymentEligibilityPolicy.evaluate(
            self.payable(AccountsPayableStatus.PARTIALLY_PAID),
        )
        self.assertTrue(result.eligible)
        self.assertIsNone(result.reason)

    def test_paid_is_ineligible_with_already_paid_reason(self):
        result = AccountsPayablePaymentEligibilityPolicy.evaluate(
            self.payable(AccountsPayableStatus.PAID),
        )
        self.assertFalse(result.eligible)
        self.assertEqual(
            result.reason,
            AccountsPayablePaymentEligibilityReason.ALREADY_PAID,
        )

    def test_cancelled_is_ineligible_with_cancelled_reason(self):
        result = AccountsPayablePaymentEligibilityPolicy.evaluate(
            self.payable(AccountsPayableStatus.CANCELLED),
        )
        self.assertFalse(result.eligible)
        self.assertEqual(result.reason, AccountsPayablePaymentEligibilityReason.CANCELLED)
