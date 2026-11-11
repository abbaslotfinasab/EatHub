from contextlib import nullcontext
from types import SimpleNamespace
from unittest import TestCase
from uuid import UUID, uuid5

from inventory.application.context import InventoryExecutionContext
from inventory.application.exceptions import InvalidApplicationInput, OperationConflict
from inventory.application.use_cases.manage_reservations import ManageReservations
from inventory.domain.enums.reservation import ReservationStatus


_NAMESPACE = UUID("90144542-95ef-4eef-a498-0e73f429725d")


class FakeRepository:
    def __init__(self, active=None, total=None):
        self.active = list(active or [])
        self.total = len(self.active) if total is None else total
        self.release_calls = []

    def list_for_business(self, business_id, **kwargs):
        self.list_kwargs = kwargs
        return self.total, self.active[:kwargs["page_size"]]

    def get_for_business(self, business_id, reservation_id, *, lock=False):
        return next((row for row in self.active if row.id == reservation_id), None)

    def release(self, business_id, reservation_id, actor_id, idempotency_key, reason):
        self.release_calls.append((business_id, reservation_id, actor_id, idempotency_key, reason))
        return SimpleNamespace(id=reservation_id, status=ReservationStatus.RELEASED)


class FakeUnitOfWork:
    def atomic(self):
        return nullcontext()


class ReleaseOrderReservationTests(TestCase):
    def setUp(self):
        self.context = InventoryExecutionContext(business_id=7, actor_id=12)
        self.reservation = SimpleNamespace(id=41, status=ReservationStatus.ACTIVE)

    def use_case(self, repository):
        return ManageReservations(repository, FakeUnitOfWork())

    def test_releases_the_only_active_order_reservation_with_stable_key(self):
        repository = FakeRepository([self.reservation])

        result = self.use_case(repository).release_for_order(
            self.context, 21, "Order cancelled"
        )

        self.assertEqual(result.id, 41)
        self.assertEqual(repository.list_kwargs["page_size"], 2)
        self.assertEqual(
            repository.release_calls,
            [(7, 41, 12, uuid5(_NAMESPACE, "release:41"), "Order cancelled")],
        )

    def test_missing_active_reservation_is_a_noop(self):
        repository = FakeRepository()

        result = self.use_case(repository).release_for_order(
            self.context, 21, "Order refunded"
        )

        self.assertIsNone(result)
        self.assertEqual(repository.release_calls, [])

    def test_missing_reservation_is_noop_without_actor(self):
        repository = FakeRepository()
        context = InventoryExecutionContext(business_id=7, actor_id=None)

        result = self.use_case(repository).release_for_order(
            context, 21, "Order refunded"
        )

        self.assertIsNone(result)
        self.assertEqual(repository.release_calls, [])

    def test_multiple_active_reservations_require_reconciliation(self):
        repository = FakeRepository([self.reservation, SimpleNamespace(id=42)], total=2)

        with self.assertRaises(OperationConflict):
            self.use_case(repository).release_for_order(
                self.context, 21, "Order cancelled"
            )

        self.assertEqual(repository.release_calls, [])

    def test_invalid_order_id_is_rejected_before_repository_access(self):
        repository = FakeRepository()

        with self.assertRaises(InvalidApplicationInput):
            self.use_case(repository).release_for_order(
                self.context, True, "Order cancelled"
            )

        self.assertFalse(hasattr(repository, "list_kwargs"))
