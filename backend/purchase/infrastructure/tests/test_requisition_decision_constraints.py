from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import Business, User
from purchase.models import PurchaseRequisition, PurchaseRequisitionDecision


class PurchaseRequisitionDecisionConstraintTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.business = Business.objects.create(name="Decision Constraint Tests")
        cls.actor = User.objects.create_user(
            email="decision-constraint@example.com",
            password="unused",
            name="Decision Actor",
            number="decision-constraint",
        )

    def create_rejection(self, reason):
        requisition = PurchaseRequisition.objects.create(
            business=self.business,
            requested_by=self.actor,
            status=PurchaseRequisition.Status.REJECTED,
        )
        return PurchaseRequisitionDecision.objects.create(
            requisition=requisition,
            decision=PurchaseRequisitionDecision.Decision.REJECTED,
            actor=self.actor,
            previous_status=PurchaseRequisition.Status.SUBMITTED,
            resulting_status=PurchaseRequisition.Status.REJECTED,
            rejection_reason=reason,
        )

    def test_database_constraint_accepts_null_reason(self):
        decision = self.create_rejection(None)

        self.assertIsNone(decision.rejection_reason)

    def test_database_constraint_accepts_empty_reason(self):
        decision = self.create_rejection("")

        self.assertEqual(decision.rejection_reason, "")

    def test_database_constraint_accepts_exactly_2000_characters(self):
        reason = "x" * 2000

        decision = self.create_rejection(reason)

        self.assertEqual(decision.rejection_reason, reason)

    def test_database_constraint_rejects_2001_characters(self):
        requisition = PurchaseRequisition.objects.create(
            business=self.business,
            requested_by=self.actor,
            status=PurchaseRequisition.Status.REJECTED,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PurchaseRequisitionDecision.objects.create(
                    requisition=requisition,
                    decision=PurchaseRequisitionDecision.Decision.REJECTED,
                    actor=self.actor,
                    previous_status=PurchaseRequisition.Status.SUBMITTED,
                    resulting_status=PurchaseRequisition.Status.REJECTED,
                    rejection_reason="x" * 2001,
                )
