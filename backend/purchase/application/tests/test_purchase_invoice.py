from contextlib import nullcontext
from datetime import date, datetime
from decimal import Decimal

from django.test import SimpleTestCase

from purchase.application.dto.purchase_invoice import (
    ApprovePurchaseInvoiceDTO,
)
from purchase.application.use_cases.purchase_invoice.approve_purchase_invoice import (
    ApprovePurchaseInvoiceUseCase,
)
from purchase.domain.entities.purchase_invoice import (
    PurchaseInvoice,
    PurchaseInvoiceItem,
)
from purchase.domain.enums.purchase_invoice_status import PurchaseInvoiceStatus


class FakeTransactionManager:
    def atomic(self):
        return nullcontext()


class FakePurchaseInvoiceRepository:
    def __init__(self, invoice):
        self.invoice = invoice
        self.save_calls = 0

    def get_by_id_for_business(self, invoice_id, business_id):
        if self.invoice.id != invoice_id or self.invoice.business_id != business_id:
            return None
        return self.invoice

    def save_approved(self, invoice):
        self.save_calls += 1
        self.invoice = invoice
        return invoice


class PurchaseInvoiceApprovalUseCaseTests(SimpleTestCase):
    def invoice(self, business_id=1):
        return PurchaseInvoice(
            id=10,
            business_id=business_id,
            supplier_id=2,
            invoice_number="INV-1",
            invoice_date=date(2026, 9, 10),
            purchase_order_id=3,
            items=[
                PurchaseInvoiceItem(
                    ingredient_id=4,
                    quantity=Decimal("1.000"),
                    unit_price=Decimal("10.00"),
                    purchase_order_item_id=20,
                )
            ],
        )

    def test_approval_updates_only_invoice_lifecycle(self):
        invoice = self.invoice()
        repository = FakePurchaseInvoiceRepository(invoice)
        use_case = ApprovePurchaseInvoiceUseCase(
            repository,
            FakeTransactionManager(),
        )

        approved = use_case.execute(
            ApprovePurchaseInvoiceDTO(
                business_id=1,
                purchase_invoice_id=10,
                approved_by_id=8,
                approved_at=datetime(2026, 9, 10, 12, 0),
            )
        )

        self.assertEqual(approved.status, PurchaseInvoiceStatus.APPROVED)
        self.assertEqual(repository.save_calls, 1)
        self.assertEqual(approved.total_price, Decimal("10.00"))

    def test_cross_business_invoice_cannot_be_approved(self):
        repository = FakePurchaseInvoiceRepository(self.invoice(business_id=2))
        use_case = ApprovePurchaseInvoiceUseCase(
            repository,
            FakeTransactionManager(),
        )

        with self.assertRaisesRegex(ValueError, "does not exist"):
            use_case.execute(
                ApprovePurchaseInvoiceDTO(
                    business_id=1,
                    purchase_invoice_id=10,
                    approved_by_id=8,
                    approved_at=datetime(2026, 9, 10, 12, 0),
                )
            )

    def test_already_approved_invoice_cannot_be_approved(self):
        invoice = self.invoice()
        invoice.approve(8, datetime(2026, 9, 10, 12, 0))
        repository = FakePurchaseInvoiceRepository(invoice)
        use_case = ApprovePurchaseInvoiceUseCase(
            repository,
            FakeTransactionManager(),
        )

        with self.assertRaisesRegex(ValueError, "cannot be approved"):
            use_case.execute(
                ApprovePurchaseInvoiceDTO(
                    business_id=1,
                    purchase_invoice_id=10,
                    approved_by_id=8,
                    approved_at=datetime(2026, 9, 10, 13, 0),
                )
            )
