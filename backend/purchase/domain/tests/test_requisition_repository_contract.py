from typing import get_type_hints
from unittest import TestCase

from purchase.domain.entities.requisition import PurchaseRequisitionDecision
from purchase.domain.repositories.requisition_repository import (
    RequisitionRepository,
)


class RequisitionRepositoryContractTests(TestCase):
    def test_decision_history_returns_a_list_of_decision_entities(self) -> None:
        return_type = get_type_hints(
            RequisitionRepository.list_decisions_for_business
        )["return"]

        self.assertEqual(return_type, list[PurchaseRequisitionDecision])
