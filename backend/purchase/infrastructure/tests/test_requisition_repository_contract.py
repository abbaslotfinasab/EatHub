from typing import get_type_hints

from django.test import SimpleTestCase

from purchase.domain.entities.requisition import PurchaseRequisitionDecision
from purchase.infrastructure.persistence.django.repositories.requisition_repository import (
    DjangoRequisitionRepository,
)


class DjangoRequisitionRepositoryContractTests(SimpleTestCase):
    databases = set()

    def test_decision_history_returns_a_list_of_decision_entities(self) -> None:
        return_type = get_type_hints(
            DjangoRequisitionRepository.list_decisions_for_business
        )["return"]

        self.assertEqual(return_type, list[PurchaseRequisitionDecision])
