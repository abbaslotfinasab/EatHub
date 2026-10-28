import unittest
from uuid import uuid4

from inventory.application.context import InventoryExecutionContext
from inventory.application.exceptions import InvalidApplicationInput
from inventory.application.use_cases.manage_reservations import ManageReservations


class ReservationSourcePolicyTests(unittest.TestCase):
    def setUp(self):
        # Source validation must fail before the use case opens a transaction
        # or calls a repository.
        self.use_case = ManageReservations(reservations=None, unit_of_work=None)
        self.context = InventoryExecutionContext(business_id=1, actor_id=10)
        self.lines = [{"ingredient_id": 2, "quantity": "1", "unit": "kg"}]

    def create(self, *, source_type="manual", source_id=None, lines=None):
        return self.use_case.create(
            self.context,
            warehouse_id=3,
            source_type=source_type,
            source_id=source_id,
            reason="Manual reservation",
            idempotency_key=uuid4(),
            lines=self.lines if lines is None else lines,
        )

    def test_unsupported_source_type_is_rejected_before_repository_access(self):
        with self.assertRaises(InvalidApplicationInput):
            self.create(source_type="order", source_id=99)

    def test_manual_source_id_is_rejected_before_repository_access(self):
        with self.assertRaises(InvalidApplicationInput):
            self.create(source_id=99)

    def test_manual_source_line_id_is_rejected_before_repository_access(self):
        with self.assertRaises(InvalidApplicationInput):
            self.create(lines=[{
                "ingredient_id": 2,
                "source_line_id": 1,
                "quantity": "1",
                "unit": "kg",
            }])
