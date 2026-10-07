from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import Business
from purchase.application.dto.payment_allocation import CreatePaymentAllocationCommand
from purchase.application.use_cases.payment_allocation.create_payment_allocation import CreatePaymentAllocation
from purchase.domain.entities.supplier_payment import SupplierPayment
from purchase.domain.enums.accounts_payable_status import AccountsPayableStatus
from purchase.domain.enums.payment_method import PaymentMethod
from purchase.infrastructure.persistence.django.repositories.accounts_payable_repository import DjangoAccountsPayableRepository
from purchase.infrastructure.persistence.django.repositories.payment_allocation_repository import DjangoPaymentAllocationRepository
from purchase.infrastructure.persistence.django.repositories.supplier_payment_repository import DjangoSupplierPaymentRepository
from purchase.infrastructure.persistence.transaction import DjangoTransactionManager
from purchase.models import AccountsPayable, PaymentAllocation, PurchaseInvoice, Supplier


class PaymentAllocationInfrastructureTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Allocation Business")
        self.other_business = Business.objects.create(name="Other Allocation Business")
        self.supplier = Supplier.objects.create(business=self.business, name="Allocation Supplier")
        self.other_supplier = Supplier.objects.create(business=self.business, name="Other Supplier")
        self.other_tenant_supplier = Supplier.objects.create(business=self.other_business, name="Tenant Supplier")
        self.payable = self.create_payable("ALLOC-AP-1", self.supplier, self.business, "100.00")
        self.second_payable = self.create_payable("ALLOC-AP-2", self.supplier, self.business, "50.00")
        self.other_payable = self.create_payable("ALLOC-AP-3", self.other_tenant_supplier, self.other_business, "10.00")
        self.payment = self.create_payment(self.supplier, self.business, "100.00")
        self.other_payment = self.create_payment(self.other_tenant_supplier, self.other_business, "100.00")
        self.payables = DjangoAccountsPayableRepository()
        self.payments = DjangoSupplierPaymentRepository()
        self.allocations = DjangoPaymentAllocationRepository()
        self.use_case = CreatePaymentAllocation(
            self.payables, self.payments, self.allocations, DjangoTransactionManager(),
        )

    @staticmethod
    def create_payable(number, supplier, business, amount):
        invoice = PurchaseInvoice.objects.create(
            business=business,
            supplier=supplier,
            invoice_number=number,
            invoice_date=date(2026, 10, 1),
            subtotal=Decimal(amount),
            total_price=Decimal(amount),
        )
        return AccountsPayable.objects.create(
            business=business,
            supplier=supplier,
            source_invoice=invoice,
            amount=Decimal(amount),
        )

    @staticmethod
    def create_payment(supplier, business, amount):
        return DjangoSupplierPaymentRepository().save(SupplierPayment(
            id=None,
            business_id=business.id,
            supplier_id=supplier.id,
            amount=Decimal(amount),
            payment_date=date(2026, 10, 7),
            method=PaymentMethod.BANK_TRANSFER,
        ))

    def allocate(self, payable, payment, amount):
        return self.use_case.execute(CreatePaymentAllocationCommand(
            business_id=payable.business_id,
            accounts_payable_id=payable.id,
            supplier_payment_id=payment.id,
            amount=Decimal(amount),
            allocated_at=timezone.now(),
        )).allocation

    def test_allocation_persists_and_updates_authoritative_payable_status(self):
        saved = self.allocate(self.payable, self.payment, "40.00")
        self.assertEqual(saved.accounts_payable_id, self.payable.id)
        self.assertEqual(saved.supplier_payment_id, self.payment.id)
        self.assertEqual(self.allocations.allocated_amount_for_accounts_payable(
            self.business.id, self.payable.id,
        ), Decimal("40.00"))
        self.assertEqual(self.allocations.allocated_amount_for_supplier_payment(
            self.business.id, self.payment.id,
        ), Decimal("40.00"))
        self.payable.refresh_from_db()
        self.assertEqual(self.payable.status, AccountsPayableStatus.PARTIALLY_PAID.value)

    def test_one_payment_can_settle_multiple_payables(self):
        self.allocate(self.payable, self.payment, "60.00")
        self.allocate(self.second_payable, self.payment, "40.00")
        self.payable.refresh_from_db()
        self.second_payable.refresh_from_db()
        self.assertEqual(self.payable.status, AccountsPayableStatus.PARTIALLY_PAID.value)
        self.assertEqual(self.second_payable.status, AccountsPayableStatus.PARTIALLY_PAID.value)
        self.assertEqual(self.allocations.allocated_amount_for_supplier_payment(
            self.business.id, self.payment.id,
        ), Decimal("100.00"))
        with self.assertRaisesRegex(ValueError, "remaining amount"):
            self.allocate(self.second_payable, self.payment, "1.00")

    def test_multiple_payments_can_settle_one_payable(self):
        self.allocate(self.payable, self.payment, "40.00")
        second_payment = self.create_payment(self.supplier, self.business, "60.00")
        self.allocate(self.payable, second_payment, "60.00")
        self.payable.refresh_from_db()
        self.assertEqual(self.payable.status, AccountsPayableStatus.PAID.value)

    def test_cross_business_references_are_hidden(self):
        with self.assertRaisesRegex(ValueError, "does not exist in this business"):
            self.use_case.execute(CreatePaymentAllocationCommand(
                business_id=self.business.id,
                accounts_payable_id=self.other_payable.id,
                supplier_payment_id=self.payment.id,
                amount=Decimal("1.00"),
                allocated_at=timezone.now(),
            ))
        with self.assertRaisesRegex(ValueError, "does not exist in this business"):
            self.allocate(self.payable, self.other_payment, "1.00")

    def test_supplier_mismatch_is_rejected(self):
        payment = self.create_payment(self.other_supplier, self.business, "100.00")
        with self.assertRaisesRegex(ValueError, "supplier does not match"):
            self.allocate(self.payable, payment, "1.00")

    def test_cancelled_payable_and_over_allocations_are_rejected(self):
        AccountsPayable.objects.filter(id=self.payable.id).update(status=AccountsPayableStatus.CANCELLED.value)
        with self.assertRaisesRegex(ValueError, "cancelled"):
            self.allocate(self.payable, self.payment, "1.00")
        AccountsPayable.objects.filter(id=self.payable.id).update(status=AccountsPayableStatus.OPEN.value)
        with self.assertRaisesRegex(ValueError, "outstanding amount"):
            self.allocate(self.payable, self.payment, "101.00")

    def test_reads_are_business_scoped_and_lists_are_filtered(self):
        saved = self.allocate(self.payable, self.payment, "20.00")
        self.assertIsNone(self.allocations.get_by_id_for_business(saved.id, self.other_business.id))
        self.assertEqual(self.allocations.get_by_id_for_business(saved.id, self.business.id).id, saved.id)
        self.assertEqual([row.id for row in self.allocations.list(
            self.business.id, accounts_payable_id=self.payable.id,
        )], [saved.id])
        self.assertEqual(self.allocations.list(self.other_business.id), [])

    def test_database_rejects_nonpositive_allocation(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PaymentAllocation.objects.create(
                    business=self.business,
                    accounts_payable=self.payable,
                    payment_id=self.payment.id,
                    amount=Decimal("0.00"),
                    allocated_at=timezone.now(),
                )

    def test_ap_status_failure_rolls_back_allocation_row(self):
        with patch.object(self.payables, "save_payment_status", side_effect=RuntimeError("forced AP update failure")):
            with self.assertRaisesRegex(RuntimeError, "forced AP update failure"):
                self.allocate(self.payable, self.payment, "25.00")
        self.assertEqual(PaymentAllocation.objects.count(), 0)
        self.payable.refresh_from_db()
        self.assertEqual(self.payable.status, AccountsPayableStatus.OPEN.value)

    def test_lock_queries_are_tenant_scoped_and_do_not_join_nullable_relations(self):
        import inspect

        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with transaction.atomic(), CaptureQueriesContext(connection) as captured:
            self.payables.lock_for_payment_allocation(self.business.id, self.payable.id)
            self.payments.lock_for_allocation(self.business.id, self.payment.id)
        sql = " ".join(query["sql"].lower() for query in captured.captured_queries)
        self.assertIn("purchase_accountspayable", sql)
        self.assertIn("purchase_supplierpayment", sql)
        self.assertIn("business_id", sql)
        self.assertNotIn(" join ", sql)
        self.assertIn(
            'select_for_update(of=("self",))',
            inspect.getsource(DjangoAccountsPayableRepository.lock_for_payment_allocation),
        )
        self.assertIn(
            'select_for_update(of=("self",))',
            inspect.getsource(DjangoSupplierPaymentRepository.lock_for_allocation),
        )
