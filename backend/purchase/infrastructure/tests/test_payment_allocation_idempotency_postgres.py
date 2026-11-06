from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from threading import Barrier
from unittest import skipUnless
from uuid import uuid4

from django.db import connection, connections
from django.db.models import Sum
from django.test import TransactionTestCase
from django.utils import timezone

from accounts.models import Business
from purchase.application.dto.payment_allocation import CreatePaymentAllocationCommand
from purchase.application.use_cases.payment_allocation.create_payment_allocation import (
    CreatePaymentAllocation,
)
from purchase.domain.enums.accounts_payable_status import AccountsPayableStatus
from purchase.infrastructure.persistence.django.repositories.accounts_payable_repository import (
    DjangoAccountsPayableRepository,
)
from purchase.infrastructure.persistence.django.repositories.payment_allocation_repository import (
    DjangoPaymentAllocationRepository,
)
from purchase.infrastructure.persistence.django.repositories.supplier_payment_repository import (
    DjangoSupplierPaymentRepository,
)
from purchase.infrastructure.persistence.transaction import DjangoTransactionManager
from purchase.models import (
    AccountsPayable,
    PaymentAllocation,
    PurchaseInvoice,
    Supplier,
    SupplierPayment,
)


@skipUnless(
    connection.vendor == "postgresql",
    "Payment allocation concurrency verification requires PostgreSQL.",
)
class PaymentAllocationIdempotencyPostgreSQLTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self) -> None:
        self.business = Business.objects.create(
            name="Payment allocation integration",
            slug="payment-allocation-integration",
        )
        self.supplier = Supplier.objects.create(
            business=self.business,
            name="Supplier",
        )
        self.invoice = self._create_invoice("INV-ALLOC-001")
        self.payable = self._create_payable(self.invoice, "100.00")
        self.payment = self._create_payment("100.00")

    def _create_invoice(self, number: str) -> PurchaseInvoice:
        return PurchaseInvoice.objects.create(
            business=self.business,
            supplier=self.supplier,
            invoice_number=number,
            invoice_date=date(2026, 11, 1),
            total_price=Decimal("100.00"),
        )

    def _create_payable(
        self,
        invoice: PurchaseInvoice,
        amount: str,
    ) -> AccountsPayable:
        return AccountsPayable.objects.create(
            business=self.business,
            supplier=self.supplier,
            source_invoice=invoice,
            amount=Decimal(amount),
            status=AccountsPayableStatus.OPEN.value,
        )

    def _create_payment(self, amount: str) -> SupplierPayment:
        return SupplierPayment.objects.create(
            business=self.business,
            supplier=self.supplier,
            amount=Decimal(amount),
            payment_date=date(2026, 11, 2),
            method="bank_transfer",
        )

    def _use_case(self) -> CreatePaymentAllocation:
        return CreatePaymentAllocation(
            DjangoAccountsPayableRepository(),
            DjangoSupplierPaymentRepository(),
            DjangoPaymentAllocationRepository(),
            DjangoTransactionManager(),
        )

    def _command(
        self,
        *,
        key=None,
        amount: str = "60.00",
        payable: AccountsPayable | None = None,
        payment: SupplierPayment | None = None,
    ) -> CreatePaymentAllocationCommand:
        return CreatePaymentAllocationCommand(
            business_id=self.business.id,
            accounts_payable_id=(payable or self.payable).id,
            supplier_payment_id=(payment or self.payment).id,
            amount=Decimal(amount),
            allocated_at=timezone.now(),
            idempotency_key=key or uuid4(),
        )

    def _run_concurrently(self, workers):
        barrier = Barrier(len(workers))

        def run(worker):
            connections.close_all()
            try:
                barrier.wait(timeout=15)
                return worker()
            except Exception as error:
                return error
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=len(workers)) as executor:
            futures = [executor.submit(run, worker) for worker in workers]
            return [future.result(timeout=30) for future in futures]

    def test_retry_after_commit_replays_the_original_allocation(self) -> None:
        key = uuid4()
        command = self._command(key=key)

        first = self._use_case().execute(command)
        retry = self._use_case().execute(command)

        self.assertEqual(first.allocation.id, retry.allocation.id)
        self.assertFalse(first.replayed)
        self.assertTrue(retry.replayed)
        self.assertEqual(
            PaymentAllocation.objects.filter(
                business=self.business,
                idempotency_key=key,
            ).count(),
            1,
        )
        self.assertEqual(
            PaymentAllocation.objects.filter(
                accounts_payable=self.payable,
            ).count(),
            1,
        )

    def test_same_key_with_different_payload_is_rejected(self) -> None:
        key = uuid4()
        self._use_case().execute(self._command(key=key, amount="40.00"))

        with self.assertRaises(ValueError):
            self._use_case().execute(self._command(key=key, amount="50.00"))

        self.assertEqual(
            PaymentAllocation.objects.filter(
                business=self.business,
                idempotency_key=key,
            ).count(),
            1,
        )

    def test_concurrent_same_key_creates_one_allocation_and_replays_winner(self) -> None:
        key = uuid4()
        command = self._command(key=key)
        results = self._run_concurrently([
            lambda: self._use_case().execute(command),
            lambda: self._use_case().execute(command),
        ])

        self.assertFalse(any(isinstance(result, Exception) for result in results))
        self.assertEqual(sum(result.replayed for result in results), 1)
        self.assertEqual(results[0].allocation.id, results[1].allocation.id)
        self.assertEqual(
            PaymentAllocation.objects.filter(
                business=self.business,
                idempotency_key=key,
            ).count(),
            1,
        )

    def test_concurrent_different_keys_cannot_overallocate_one_payment(self) -> None:
        second_invoice = self._create_invoice("INV-ALLOC-002")
        second_payable = self._create_payable(second_invoice, "100.00")
        results = self._run_concurrently([
            lambda: self._use_case().execute(
                self._command(key=uuid4(), payable=self.payable, amount="60.00")
            ),
            lambda: self._use_case().execute(
                self._command(key=uuid4(), payable=second_payable, amount="60.00")
            ),
        ])

        self.assertEqual(sum(not isinstance(result, Exception) for result in results), 1)
        self.assertEqual(
            PaymentAllocation.objects.filter(payment=self.payment).aggregate(
                total=Sum("amount")
            )["total"],
            Decimal("60.00"),
        )

    def test_concurrent_different_keys_cannot_overpay_one_accounts_payable(self) -> None:
        second_payment = self._create_payment("100.00")
        results = self._run_concurrently([
            lambda: self._use_case().execute(
                self._command(key=uuid4(), payment=self.payment, amount="60.00")
            ),
            lambda: self._use_case().execute(
                self._command(key=uuid4(), payment=second_payment, amount="60.00")
            ),
        ])

        self.assertEqual(sum(not isinstance(result, Exception) for result in results), 1)
        self.assertEqual(
            PaymentAllocation.objects.filter(
                accounts_payable=self.payable,
            ).count(),
            1,
        )
        self.payable.refresh_from_db()
        self.assertEqual(self.payable.status, AccountsPayableStatus.PARTIALLY_PAID.value)
