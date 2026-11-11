from unittest import TestCase
from uuid import UUID

from inventory.application.context import InventoryExecutionContext
from inventory.application.dto.order_consumption_posting import OrderConsumptionPostingDTO
from inventory.application.use_cases.apply_order_consumption import ApplyOrderConsumption


class FakeReservations:
    def __init__(self):
        self.calls = []

    def release(self, context, reservation_id, idempotency_key, reason):
        self.calls.append(("release", reservation_id, idempotency_key, reason))

    def create_for_order(self, context, **kwargs):
        self.calls.append(("reserve", kwargs))


class FakePosting:
    def __init__(self, calls):
        self.calls = calls

    def post_order_issue(self, context, **kwargs):
        self.calls.append(("post", kwargs))
        return OrderConsumptionPostingDTO(71, {4: 91})


class ApplyOrderConsumptionTests(TestCase):
    def test_replaces_reservation_before_posting_and_returns_ledger_ids(self):
        calls = []
        reservations = FakeReservations()
        reservations.calls = calls
        use_case = ApplyOrderConsumption(reservations, FakePosting(calls))
        context = InventoryExecutionContext(business_id=7, actor_id=12)

        result = use_case.execute(
            context,
            order_id=21,
            consumption_id=31,
            warehouse_id=5,
            reservation_id=41,
            remaining_lines=[{"ingredient_id": 4, "quantity": "2", "unit": "kg"}],
            actual_lines=[{"ingredient_id": 4, "quantity": "1", "unit": "kg"}],
        )

        self.assertEqual([call[0] for call in calls], ["release", "reserve", "post"])
        self.assertEqual(calls[0][1], 41)
        self.assertIsInstance(calls[0][2], UUID)
        self.assertEqual(result.operation_id, 71)
        self.assertEqual(result.movement_ids_by_ingredient, {4: 91})

    def test_skips_replacement_reservation_when_nothing_remains(self):
        calls = []
        reservations = FakeReservations()
        reservations.calls = calls
        use_case = ApplyOrderConsumption(reservations, FakePosting(calls))
        context = InventoryExecutionContext(business_id=7, actor_id=12)

        use_case.execute(
            context,
            order_id=21,
            consumption_id=32,
            warehouse_id=5,
            reservation_id=41,
            remaining_lines=[],
            actual_lines=[{"ingredient_id": 4, "quantity": "1", "unit": "kg"}],
        )

        self.assertEqual([call[0] for call in calls], ["release", "post"])
