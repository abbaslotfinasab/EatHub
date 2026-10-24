import sqlite3
from types import SimpleNamespace
from unittest.mock import patch

from django.db import IntegrityError, OperationalError
from django.test import SimpleTestCase

from purchase.models import PurchaseRequisition as DjangoPurchaseRequisition
from purchase.infrastructure.persistence.django.repositories.requisition_repository import (
    DjangoRequisitionRepository,
    _is_expected_decision_integrity_conflict,
    _is_supported_decision_conflict,
)


class DriverError(Exception):
    pass


class TrackingAtomic:
    def __init__(self):
        self.exited = False

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception, traceback):
        self.exited = True
        return False


class RequisitionDecisionErrorClassificationTests(SimpleTestCase):
    @staticmethod
    def django_error_from(driver_error, error_type=OperationalError):
        try:
            raise error_type("driver failure") from driver_error
        except error_type as error:
            return error

    @staticmethod
    def django_error_with_context(driver_error, error_type):
        try:
            raise driver_error
        except DriverError:
            try:
                raise error_type("outer database error")
            except error_type as error:
                return error

    def test_unrelated_context_is_not_used_to_classify_operational_error(self):
        lock_error = DriverError("database is locked")
        lock_error.sqlite_errorcode = sqlite3.SQLITE_BUSY
        error = self.django_error_with_context(lock_error, OperationalError)
        atomic_block = TrackingAtomic()

        self.assertIsNone(error.__cause__)
        self.assertIs(error.__context__, lock_error)
        self.assertFalse(_is_supported_decision_conflict(error))

        with (
            patch(
                "purchase.infrastructure.persistence.django.repositories.requisition_repository.transaction.atomic",
                return_value=atomic_block,
            ),
            patch.object(
                DjangoPurchaseRequisition.objects,
                "select_for_update",
                side_effect=error,
            ),
        ):
            with self.assertRaises(OperationalError) as raised:
                DjangoRequisitionRepository().record_decision(
                    requisition_id=1,
                    business_id=1,
                    actor_id=2,
                    decision="approved",
                )

        self.assertIs(raised.exception, error)
        self.assertTrue(atomic_block.exited)

    def test_postgresql_lock_and_serialization_sqlstates_are_conflicts(self):
        for sqlstate in ("40001", "40P01", "55P03"):
            with self.subTest(sqlstate=sqlstate):
                driver_error = DriverError("opaque driver message")
                driver_error.pgcode = sqlstate
                self.assertTrue(
                    _is_supported_decision_conflict(
                        self.django_error_from(driver_error)
                    )
                )

    def test_sqlite_busy_and_locked_codes_are_conflicts(self):
        for code in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
            with self.subTest(sqlite_errorcode=code):
                driver_error = DriverError("opaque driver message")
                driver_error.sqlite_errorcode = code
                self.assertTrue(
                    _is_supported_decision_conflict(
                        self.django_error_from(driver_error)
                    )
                )

    def test_sqlite_extended_busy_code_is_a_conflict(self):
        driver_error = DriverError("opaque driver message")
        driver_error.sqlite_errorcode = sqlite3.SQLITE_BUSY | (2 << 8)

        self.assertTrue(
            _is_supported_decision_conflict(self.django_error_from(driver_error))
        )

    def test_unknown_error_codes_are_not_conflicts_even_with_lock_like_text(self):
        driver_error = DriverError("database is locked")
        driver_error.pgcode = "08006"

        self.assertFalse(
            _is_supported_decision_conflict(self.django_error_from(driver_error))
        )

    def test_missing_driver_error_code_is_not_a_conflict(self):
        driver_error = DriverError("database is locked")

        self.assertFalse(
            _is_supported_decision_conflict(self.django_error_from(driver_error))
        )

    def test_postgresql_decision_unique_constraint_is_a_conflict(self):
        driver_error = DriverError("unique violation")
        driver_error.pgcode = "23505"
        driver_error.diag = SimpleNamespace(
            constraint_name="pur_req_decision_uq",
        )

        self.assertTrue(
            _is_expected_decision_integrity_conflict(
                self.django_error_from(driver_error)
            )
        )

    def test_sqlite_decision_unique_code_is_a_conflict(self):
        driver_error = DriverError("unique violation")
        driver_error.sqlite_errorcode = sqlite3.SQLITE_CONSTRAINT_UNIQUE

        self.assertTrue(
            _is_expected_decision_integrity_conflict(
                self.django_error_from(driver_error)
            )
        )

    def test_unexpected_integrity_error_propagates_unchanged_after_atomic_exit(self):
        driver_error = DriverError("foreign key violation")
        driver_error.sqlite_errorcode = sqlite3.SQLITE_CONSTRAINT_FOREIGNKEY
        database_error = self.django_error_from(driver_error, IntegrityError)

        atomic_block = TrackingAtomic()
        with (
            patch(
                "purchase.infrastructure.persistence.django.repositories.requisition_repository.transaction.atomic",
                return_value=atomic_block,
            ),
            patch.object(
                DjangoPurchaseRequisition.objects,
                "select_for_update",
                side_effect=database_error,
            ),
        ):
            with self.assertRaises(IntegrityError) as raised:
                DjangoRequisitionRepository().record_decision(
                    requisition_id=1,
                    business_id=1,
                    actor_id=2,
                    decision="approved",
                )

        self.assertIs(raised.exception, database_error)
        self.assertTrue(atomic_block.exited)

    def test_recognized_decision_unique_conflict_is_translated_after_atomic_exit(self):
        driver_error = DriverError("unique violation")
        driver_error.pgcode = "23505"
        driver_error.diag = SimpleNamespace(
            constraint_name="pur_req_decision_uq",
        )
        database_error = self.django_error_from(driver_error, IntegrityError)

        atomic_block = TrackingAtomic()
        with (
            patch(
                "purchase.infrastructure.persistence.django.repositories.requisition_repository.transaction.atomic",
                return_value=atomic_block,
            ),
            patch.object(
                DjangoPurchaseRequisition.objects,
                "select_for_update",
                side_effect=database_error,
            ),
        ):
            with self.assertRaisesRegex(
                ValueError,
                "requisition decision conflicts with the current record",
            ) as raised:
                DjangoRequisitionRepository().record_decision(
                    requisition_id=1,
                    business_id=1,
                    actor_id=2,
                    decision="approved",
                )

        self.assertIs(raised.exception.__cause__, database_error)
        self.assertTrue(atomic_block.exited)
