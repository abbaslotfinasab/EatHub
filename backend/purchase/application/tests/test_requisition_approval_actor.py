from unittest import TestCase

from purchase.application.use_cases.requisition.approve_requisition import (
    ApproveRequisitionUseCase,
)
from purchase.application.use_cases.requisition.submit_requisition import (
    SubmitRequisitionUseCase,
)
from purchase.domain.entities.requisition import (
    PurchaseRequisition,
    PurchaseRequisitionItem,
)
from purchase.domain.enums.requisition_status import RequisitionStatus


class InMemoryRequisitionRepository:
    def __init__(self, requisition):
        self.requisition = requisition
        self.saved = False

    def get_by_id_for_business(self, requisition_id, business_id):
        if (
            requisition_id == self.requisition.id
            and business_id == self.requisition.business_id
        ):
            return self.requisition
        return None

    def save(self, requisition):
        self.saved = True
        return requisition

    def record_decision(
        self,
        requisition_id,
        business_id,
        actor_id,
        decision,
        rejection_reason=None,
    ):
        requisition = self.get_by_id_for_business(requisition_id, business_id)
        if requisition is None:
            raise ValueError("Requisition does not exist in this business.")
        if decision == "approved":
            requisition.approve(actor_id)
        elif decision == "rejected":
            requisition.reject()
        self.saved = True
        return requisition


class ApproveRequisitionActorTests(TestCase):
    def make_requisition(self):
        return PurchaseRequisition(
            id=21,
            business_id=7,
            requested_by_id=42,
            status=RequisitionStatus.SUBMITTED,
        )

    def test_requester_cannot_approve_their_own_requisition(self):
        repository = InMemoryRequisitionRepository(self.make_requisition())
        use_case = ApproveRequisitionUseCase(repository)

        with self.assertRaisesRegex(
            ValueError,
            r"^A requester cannot approve their own requisition\.$",
        ):
            use_case.execute(21, 7, actor_id=42)

        self.assertFalse(repository.saved)

    def test_another_actor_can_approve_the_requisition(self):
        repository = InMemoryRequisitionRepository(self.make_requisition())
        use_case = ApproveRequisitionUseCase(repository)

        approved = use_case.execute(21, 7, actor_id=99)

        self.assertEqual(approved.status, RequisitionStatus.APPROVED)
        self.assertTrue(repository.saved)

    def test_only_requester_can_submit_requisition(self):
        requisition = PurchaseRequisition(
            id=21,
            business_id=7,
            requested_by_id=42,
            status=RequisitionStatus.DRAFT,
            items=[PurchaseRequisitionItem(ingredient_id=3, quantity=1)],
        )
        repository = InMemoryRequisitionRepository(requisition)
        use_case = SubmitRequisitionUseCase(repository)

        with self.assertRaisesRegex(
            ValueError,
            r"^Only the requester can submit this requisition\.$",
        ):
            use_case.execute(21, 7, requester_id=99)

        self.assertFalse(repository.saved)
