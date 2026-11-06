from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from threading import Barrier
from unittest import skipUnless
from uuid import uuid4

from django.db import IntegrityError, connection, connections, transaction
from django.test import TransactionTestCase

from accounts.models import Business
from purchase.application.dto.supplier_payment import CreateSupplierPaymentDTO
from purchase.application.exceptions import SupplierPaymentIdempotencyPayloadMismatch
from purchase.application.use_cases.supplier_payment.create_supplier_payment import (
    CreateSupplierPaymentUseCase,
)
from purchase.domain.enums.payment_method import PaymentMethod
from purchase.infrastructure.persistence.django.repositories.supplier_payment_repository import (
    DjangoSupplierPaymentRepository,
)
from purchase.infrastructure.persistence.django.repositories.supplier_repository import (
    DjangoSupplierRepository,
)
from purchase.models import Supplier, SupplierPayment


@skipUnless(
    connection.vendor == "postgresql",
    "Supplier payment concurrency verification requires PostgreSQL.",
)
class SupplierPaymentIdempotencyPostgreSQLTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.business = Business.objects.create(
            name="Supplier payment idempotency",
            slug="supplier-payment-idempotency",
        )
        self.supplier = Supplier.objects.create(
            business=self.business,
            name="Supplier",
        )

    def _command(self, *, key=None, amount="100.00", supplier=None, method=PaymentMethod.BANK_TRANSFER):
        return CreateSupplierPaymentDTO(
            business_id=self.business.id,
            supplier_id=(supplier or self.supplier).id,
            amount=Decimal(amount),
            payment_date=date(2026, 11, 6),
            method=method,
            idempotency_key=key or uuid4(),
        )

    def _use_case(self, repository=None):
        return CreateSupplierPaymentUseCase(
            repository or DjangoSupplierPaymentRepository(),
            DjangoSupplierRepository(),
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

    def test_retry_after_commit_replays_original_payment(self):
        key = uuid4()
        command = self._command(key=key)

        first, first_replayed = self._use_case().execute(command)
        retry, retry_replayed = self._use_case().execute(command)

        self.assertFalse(first_replayed)
        self.assertTrue(retry_replayed)
        self.assertEqual(first.id, retry.id)
        self.assertEqual(
            SupplierPayment.objects.filter(
                business=self.business,
                idempotency_key=key,
            ).count(),
            1,
        )

    def test_same_key_with_different_payload_is_rejected(self):
        key = uuid4()
        self._use_case().execute(self._command(key=key, amount="100.00"))

        with self.assertRaises(SupplierPaymentIdempotencyPayloadMismatch):
            self._use_case().execute(self._command(key=key, amount="90.00"))

        self.assertEqual(SupplierPayment.objects.count(), 1)

    def test_concurrent_same_key_creates_one_payment_and_replays_winner(self):
        key = uuid4()
        command = self._command(key=key)
        results = self._run_concurrently([
            lambda: self._use_case().execute(command),
            lambda: self._use_case().execute(command),
        ])

        self.assertFalse(any(isinstance(result, Exception) for result in results))
        self.assertEqual(sum(result[1] for result in results), 1)
        self.assertEqual(results[0][0].id, results[1][0].id)
        self.assertEqual(
            SupplierPayment.objects.filter(
                business=self.business,
                idempotency_key=key,
            ).count(),
            1,
        )

    def test_concurrent_same_key_with_different_payload_has_one_winner(self):
        key = uuid4()
        results = self._run_concurrently([
            lambda: self._use_case().execute(self._command(key=key, amount="40.00")),
            lambda: self._use_case().execute(self._command(key=key, amount="50.00")),
        ])

        self.assertEqual(sum(not isinstance(result, Exception) for result in results), 1)
        self.assertEqual(
            sum(isinstance(result, SupplierPaymentIdempotencyPayloadMismatch) for result in results),
            1,
        )
        self.assertEqual(
            SupplierPayment.objects.filter(
                business=self.business,
                idempotency_key=key,
            ).count(),
            1,
        )

    def test_database_rejects_partial_idempotency_metadata(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SupplierPayment.objects.create(
                business=self.business,
                supplier=self.supplier,
                amount=Decimal("10.00"),
                payment_date=date(2026, 11, 6),
                method=PaymentMethod.CASH.value,
                idempotency_key=uuid4(),
                payload_fingerprint=None,
                payload_version=None,
            )

    def test_failed_insert_does_not_claim_key_and_retry_succeeds(self):
        key = uuid4()
        command = self._command(key=key)
        repository = DjangoSupplierPaymentRepository()
        original_save = SupplierPayment.save

        def fail_once(instance, *args, **kwargs):
            if instance.idempotency_key == key:
                raise RuntimeError("simulated persistence failure")
            return original_save(instance, *args, **kwargs)

        from unittest.mock import patch

        with patch.object(SupplierPayment, "save", new=fail_once):
            with self.assertRaises(RuntimeError):
                self._use_case(repository).execute(command)

        self.assertFalse(
            SupplierPayment.objects.filter(
                business=self.business,
                idempotency_key=key,
            ).exists()
        )
        payment, replayed = self._use_case(repository).execute(command)
        self.assertFalse(replayed)
        self.assertIsNotNone(payment.id)
        self.assertEqual(SupplierPayment.objects.count(), 1)
