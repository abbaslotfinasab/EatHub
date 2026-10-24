from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.db import close_old_connections
from django.test import TransactionTestCase, skipUnlessDBFeature

from accounts.models import Business, User
from purchase.models import (
    PurchaseRequisition,
    PurchaseRequisitionDecision,
)
from purchase.infrastructure.persistence.django.repositories.requisition_repository import (
    DjangoRequisitionRepository,
)


class PurchaseRequisitionDecisionConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.business = Business.objects.create(name="Decision Concurrency")
        self.requester = User.objects.create_user(
            email="decision-requester@example.com",
            password="unused",
            name="Requester",
            number="decision-requester",
        )
        self.approver = User.objects.create_user(
            email="decision-approver@example.com",
            password="unused",
            name="Approver",
            number="decision-approver",
        )
        self.rejector = User.objects.create_user(
            email="decision-rejector@example.com",
            password="unused",
            name="Rejector",
            number="decision-rejector",
        )
        self.requisition = PurchaseRequisition.objects.create(
            business=self.business,
            requested_by=self.requester,
            status=PurchaseRequisition.Status.SUBMITTED,
        )

    @skipUnlessDBFeature("has_select_for_update")
    def test_competing_decisions_persist_only_one_transition(self):
        start = Barrier(2)

        def decide(actor_id, decision):
            close_old_connections()
            try:
                start.wait(timeout=10)
                result = DjangoRequisitionRepository().record_decision(
                    requisition_id=self.requisition.id,
                    business_id=self.business.id,
                    actor_id=actor_id,
                    decision=decision,
                )
                return "success", result.status.value
            except ValueError:
                return "conflict", None
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(
                lambda args: decide(*args),
                [
                    (self.approver.id, PurchaseRequisitionDecision.Decision.APPROVED),
                    (self.rejector.id, PurchaseRequisitionDecision.Decision.REJECTED),
                ],
            ))

        self.assertEqual(sum(result[0] == "success" for result in results), 1)
        self.assertEqual(sum(result[0] == "conflict" for result in results), 1)
        persisted = PurchaseRequisition.objects.get(pk=self.requisition.id)
        decisions = PurchaseRequisitionDecision.objects.filter(
            requisition=self.requisition,
        )
        self.assertEqual(decisions.count(), 1)
        self.assertEqual(persisted.status, decisions.get().resulting_status)
