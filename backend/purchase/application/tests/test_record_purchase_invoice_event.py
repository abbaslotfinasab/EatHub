from unittest import TestCase

from purchase.application.dto.purchase_invoice_event import RecordPurchaseInvoiceEventDTO
from purchase.application.use_cases.purchase_invoice.record_purchase_invoice_event import (
    RecordPurchaseInvoiceEventUseCase,
)


class RecordPurchaseInvoiceEventUseCaseTests(TestCase):
    def test_delegates_complete_event_dto_to_repository(self):
        class Repository:
            def __init__(self):
                self.received = None

            def create(self, data):
                self.received = data

        repository = Repository()
        data = RecordPurchaseInvoiceEventDTO(
            business_id=7,
            purchase_invoice_id=19,
            actor_id=23,
            event_type="approved",
            previous_status="draft",
            resulting_status="approved",
            metadata={"approved_at": "2026-11-23T12:00:00+00:00"},
        )

        RecordPurchaseInvoiceEventUseCase(repository).execute(data)

        self.assertIs(repository.received, data)
