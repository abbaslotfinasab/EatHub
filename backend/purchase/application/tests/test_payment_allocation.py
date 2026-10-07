from contextlib import contextmanager
from datetime import date, datetime, timezone
from decimal import Decimal

from django.test import SimpleTestCase

from purchase.application.dto.payment_allocation import CreatePaymentAllocationCommand
from purchase.application.use_cases.payment_allocation.create_payment_allocation import CreatePaymentAllocation
from purchase.domain.entities.accounts_payable import AccountsPayable
from purchase.domain.entities.supplier_payment import SupplierPayment
from purchase.domain.enums.accounts_payable_status import AccountsPayableStatus
from purchase.domain.enums.payment_method import PaymentMethod


class FakeTransactionManager:
    @contextmanager
    def atomic(self):
        yield


class FakeAccountsPayableRepository:
    def __init__(self, payable):
        self.payable = payable
        self.locked = []
        self.saved_statuses = []

    def lock_for_payment_allocation(self, business_id, payable_id):
        self.locked.append(("ap", business_id, payable_id))
        return self.payable is not None and (self.payable.business_id, self.payable.id) == (business_id, payable_id)

    def get_by_id_for_business(self, payable_id, business_id):
        if self.payable and (self.payable.id, self.payable.business_id) == (payable_id, business_id):
            return self.payable
        return None

    def save_payment_status(self, payable_id, business_id, status):
        self.saved_statuses.append(status)
        self.payable.status = status


class FakeSupplierPaymentRepository:
    def __init__(self, payment):
        self.payment = payment

    def lock_for_allocation(self, business_id, payment_id):
        return self.payment is not None and (self.payment.business_id, self.payment.id) == (business_id, payment_id)

    def get_by_id_for_business(self, payment_id, business_id):
        if self.payment and (self.payment.id, self.payment.business_id) == (payment_id, business_id):
            return self.payment
        return None


class FakeAllocationRepository:
    def __init__(self, ap_total=Decimal("0.00"), payment_total=Decimal("0.00")):
        self.ap_total = ap_total
        self.payment_total = payment_total
        self.rows = []

    def allocated_amount_for_accounts_payable(self, business_id, payable_id):
        return self.ap_total

    def allocated_amount_for_supplier_payment(self, business_id, payment_id):
        return self.payment_total

    def create(self, allocation):
        from dataclasses import replace

        saved = replace(allocation, id=len(self.rows) + 1)
        self.rows.append(saved)
        self.ap_total += allocation.amount
        self.payment_total += allocation.amount
        return saved


class CreatePaymentAllocationTests(SimpleTestCase):
    def setUp(self):
        self.payable = AccountsPayable(
            id=11, business_id=1, supplier_id=3, source_invoice_id=21,
            amount=Decimal("100.00"),
        )
        self.payment = SupplierPayment(
            id=12, business_id=1, supplier_id=3, amount=Decimal("150.00"),
            payment_date=date(2026, 10, 7), method=PaymentMethod.CASH,
        )
        self.payables = FakeAccountsPayableRepository(self.payable)
        self.payments = FakeSupplierPaymentRepository(self.payment)
        self.allocations = FakeAllocationRepository()
        self.use_case = CreatePaymentAllocation(
            self.payables, self.payments, self.allocations, FakeTransactionManager(),
        )
        self.command = CreatePaymentAllocationCommand(
            business_id=1, accounts_payable_id=11, supplier_payment_id=12,
            amount=Decimal("40.00"), allocated_at=datetime(2026, 10, 7, tzinfo=timezone.utc),
        )

    def test_allocation_success_updates_ap_to_partially_paid(self):
        result = self.use_case.execute(self.command)
        self.assertEqual(result.allocation.amount, Decimal("40.00"))
        self.assertEqual(self.payable.status, AccountsPayableStatus.PARTIALLY_PAID)
        self.assertEqual(self.payables.saved_statuses, [AccountsPayableStatus.PARTIALLY_PAID])
        self.assertEqual(self.payables.locked, [("ap", 1, 11)])

    def test_full_allocation_updates_ap_to_paid(self):
        result = self.use_case.execute(CreatePaymentAllocationCommand(
            **{**self.command.__dict__, "amount": Decimal("100.00")},
        ))
        self.assertEqual(result.allocation.amount, Decimal("100.00"))
        self.assertEqual(self.payable.status, AccountsPayableStatus.PAID)

    def test_ap_and_payment_remaining_balances_are_enforced(self):
        with self.assertRaisesRegex(ValueError, "outstanding amount"):
            self.use_case.execute(CreatePaymentAllocationCommand(
                **{**self.command.__dict__, "amount": Decimal("101.00")},
            ))
        self.allocations.payment_total = Decimal("120.00")
        with self.assertRaisesRegex(ValueError, "remaining amount"):
            self.use_case.execute(CreatePaymentAllocationCommand(
                **{**self.command.__dict__, "amount": Decimal("40.00")},
            ))

    def test_supplier_mismatch_is_rejected(self):
        self.payment.supplier_id = 4
        with self.assertRaisesRegex(ValueError, "supplier does not match"):
            self.use_case.execute(self.command)

    def test_cross_business_references_are_not_found(self):
        self.command = CreatePaymentAllocationCommand(
            **{**self.command.__dict__, "business_id": 2},
        )
        with self.assertRaisesRegex(ValueError, "does not exist in this business"):
            self.use_case.execute(self.command)

    def test_cancelled_and_already_paid_payables_are_rejected(self):
        self.payable.status = AccountsPayableStatus.CANCELLED
        with self.assertRaisesRegex(ValueError, "cancelled"):
            self.use_case.execute(self.command)
        self.payable.status = AccountsPayableStatus.OPEN
        self.allocations.ap_total = Decimal("100.00")
        with self.assertRaisesRegex(ValueError, "fully paid"):
            self.use_case.execute(self.command)

    def test_missing_payment_is_not_found(self):
        self.payments.payment = None
        with self.assertRaisesRegex(ValueError, "Supplier payment does not exist"):
            self.use_case.execute(self.command)

    def test_allocation_requires_positive_decimal(self):
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            self.use_case.execute(CreatePaymentAllocationCommand(
                **{**self.command.__dict__, "amount": Decimal("0.00")},
            ))
