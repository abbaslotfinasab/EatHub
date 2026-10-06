from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase

from purchase.application.dto.accounts_payable_payment_eligibility import (
    GetAccountsPayablePaymentEligibilityQuery,
)
from purchase.application.use_cases.accounts_payable.get_accounts_payable_payment_eligibility import (
    GetAccountsPayablePaymentEligibility,
)
from purchase.domain.entities.accounts_payable import AccountsPayable
from purchase.domain.enums.accounts_payable_payment_eligibility_reason import (
    AccountsPayablePaymentEligibilityReason,
)
from purchase.domain.enums.accounts_payable_status import AccountsPayableStatus


class FakeAccountsPayableRepository:
    def __init__(self, payable):
        self.payable = payable
        self.calls = []

    def get_by_id_for_business(self, accounts_payable_id, business_id):
        self.calls.append((accounts_payable_id, business_id))
        if self.payable is None:
            return None
        if (self.payable.id, self.payable.business_id) != (accounts_payable_id, business_id):
            return None
        return self.payable


class GetAccountsPayablePaymentEligibilityTests(SimpleTestCase):
    def payable(self, status=AccountsPayableStatus.OPEN):
        return AccountsPayable(
            id=8,
            business_id=1,
            supplier_id=2,
            source_invoice_id=3,
            amount=Decimal("12500000.00"),
            due_date=date(2026, 11, 15),
            status=status,
        )

    def query(self, business_id=1, payable_id=8):
        return GetAccountsPayablePaymentEligibilityQuery(
            business_id=business_id,
            accounts_payable_id=payable_id,
        )

    def test_returns_eligibility_from_tenant_scoped_repository_read(self):
        payable = self.payable(AccountsPayableStatus.PARTIALLY_PAID)
        repository = FakeAccountsPayableRepository(payable)
        result = GetAccountsPayablePaymentEligibility(repository).execute(self.query())

        self.assertEqual(repository.calls, [(8, 1)])
        self.assertEqual(result.accounts_payable_id, 8)
        self.assertTrue(result.eligible)
        self.assertEqual(result.status, AccountsPayableStatus.PARTIALLY_PAID)
        self.assertEqual(result.amount, Decimal("12500000.00"))
        self.assertIsNone(result.reason)
        self.assertEqual(payable.status, AccountsPayableStatus.PARTIALLY_PAID)

    def test_paid_result_contains_already_paid_reason(self):
        result = GetAccountsPayablePaymentEligibility(
            FakeAccountsPayableRepository(self.payable(AccountsPayableStatus.PAID)),
        ).execute(self.query())
        self.assertFalse(result.eligible)
        self.assertEqual(result.reason, AccountsPayablePaymentEligibilityReason.ALREADY_PAID)

    def test_cancelled_result_contains_cancelled_reason(self):
        result = GetAccountsPayablePaymentEligibility(
            FakeAccountsPayableRepository(self.payable(AccountsPayableStatus.CANCELLED)),
        ).execute(self.query())
        self.assertFalse(result.eligible)
        self.assertEqual(result.reason, AccountsPayablePaymentEligibilityReason.CANCELLED)

    def test_other_tenant_and_missing_payable_are_not_found(self):
        use_case = GetAccountsPayablePaymentEligibility(
            FakeAccountsPayableRepository(self.payable()),
        )
        with self.assertRaisesRegex(ValueError, "does not exist in this business"):
            use_case.execute(self.query(business_id=2))
        with self.assertRaisesRegex(ValueError, "does not exist in this business"):
            GetAccountsPayablePaymentEligibility(
                FakeAccountsPayableRepository(None),
            ).execute(self.query())

    def test_ids_must_be_positive(self):
        use_case = GetAccountsPayablePaymentEligibility(
            FakeAccountsPayableRepository(self.payable()),
        )
        with self.assertRaisesRegex(ValueError, "Business ID"):
            use_case.execute(self.query(business_id=0))
        with self.assertRaisesRegex(ValueError, "Accounts payable ID"):
            use_case.execute(self.query(payable_id=0))
