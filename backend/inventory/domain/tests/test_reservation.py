import unittest

from inventory.domain.entities.reservation import ReservationLine, ReservationRequest, release_reservation
from inventory.domain.enums.reservation import ReservationStatus
from inventory.domain.exceptions import InvalidReservation
from inventory.domain.value_objects.quantity import Quantity
from inventory.domain.value_objects.unit import Unit


class ReservationDomainTests(unittest.TestCase):
    def line(self, ingredient_id=1, source_line_id=None):
        return ReservationLine(ingredient_id, Quantity("1.25", Unit.KG), source_line_id)

    def test_request_accepts_manual_reservation_without_external_source(self):
        request = ReservationRequest(
            business_id=1,
            warehouse_id=2,
            source_type="manual",
            source_id=None,
            reason="Manual hold",
            idempotency_key="key-1",
            lines=(self.line(),),
        )
        self.assertEqual(len(request.lines), 1)

    def test_request_accepts_order_identity_and_rejects_unsupported_or_manual_references(self):
        request = ReservationRequest(1, 2, "order", 3, "Order hold", "key-order", (self.line(),))
        self.assertEqual(request.source_id, 3)
        with self.assertRaises(InvalidReservation):
            ReservationRequest(1, 2, "purchase", 3, "Reason", "key", (self.line(),))
        with self.assertRaises(InvalidReservation):
            ReservationRequest(1, 2, "order", None, "Reason", "key", (self.line(),))
        with self.assertRaises(InvalidReservation):
            ReservationRequest(1, 2, "manual", 3, "Reason", "key", (self.line(),))
        with self.assertRaises(InvalidReservation):
            ReservationRequest(1, 2, "manual", None, "Reason", "key", (self.line(source_line_id=10),))
        with self.assertRaises(InvalidReservation):
            ReservationRequest(1, 2, "manual", None, "Reason", "key", (self.line(), self.line()))

    def test_request_rejects_invalid_identity_and_non_positive_quantity(self):
        with self.assertRaises(InvalidReservation):
            ReservationRequest(1, 2, "Order", 3, "Reason", "key", (self.line(),))
        with self.assertRaises(InvalidReservation):
            ReservationLine(1, Quantity("0", Unit.KG))

    def test_only_active_reservation_can_be_released(self):
        self.assertEqual(release_reservation(ReservationStatus.ACTIVE), ReservationStatus.RELEASED)
        with self.assertRaises(InvalidReservation):
            release_reservation(ReservationStatus.RELEASED)
