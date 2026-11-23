from unittest.mock import Mock

from django.test import SimpleTestCase

from purchase.application.dto.purchase_invoice_event import PurchaseInvoiceEventWriteDTO
from purchase.application.use_cases.purchase_invoice.record_purchase_invoice_event import (
    RecordPurchaseInvoiceEventUseCase,
)


class RecordPurchaseInvoiceEventUseCaseTests(SimpleTestCase):
    def test_delegates_complete_event_to_write_repository(self):
        event = PurchaseInvoiceEventWriteDTO(
            business_id=7,
            purchase_invoice_id=31,
            actor_id=12,
            event_type="approved",
            previous_status="draft",
            resulting_status="approved",
            metadata={"approved_at": "2026-11-23T10:00:00+00:00"},
        )
        repository = Mock()
        repository.create.return_value = 99

        result = RecordPurchaseInvoiceEventUseCase(repository).execute(event)

        self.assertEqual(result, 99)
        repository.create.assert_called_once_with(event)
