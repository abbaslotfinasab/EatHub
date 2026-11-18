from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from decimal import Decimal
from threading import Barrier
from unittest import skipUnless

from django.db import connection, connections
from django.test import TransactionTestCase

from accounts.models import Business, User
from inventory.models import Ingredient
from purchase.application.dto.purchase_invoice import ApprovePurchaseInvoiceDTO
from purchase.application.use_cases.purchase_invoice.approve_purchase_invoice import (
    ApprovePurchaseInvoiceUseCase,
)
from purchase.domain.entities.purchase_invoice import PurchaseInvoice, PurchaseInvoiceItem
from purchase.domain.enums.purchase_invoice_status import PurchaseInvoiceStatus
from purchase.infrastructure.persistence.django.repositories.purchase_invoice_repository import (
    DjangoPurchaseInvoiceRepository,
)
from purchase.infrastructure.persistence.transaction import DjangoTransactionManager
from purchase.models import PurchaseOrder, PurchaseOrderItem, Supplier


@skipUnless(connection.vendor == "postgresql", "Invoice approval race verification requires PostgreSQL.")
class PurchaseInvoiceApprovalConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.business = Business.objects.create(name="Invoice approval race", slug="invoice-approval-race")
        self.user = User.objects.create_user(
            email="invoice-approval-race@example.com",
            password="test-only",
            name="Invoice Approval",
        )
        self.supplier = Supplier.objects.create(business=self.business, name="Supplier")
        self.ingredient = Ingredient.objects.create(
            business=self.business, name="Flour", unit=Ingredient.Unit.KG,
        )
        self.order = PurchaseOrder.objects.create(
            business=self.business,
            supplier=self.supplier,
            order_date=date(2026, 11, 1),
            status=PurchaseOrder.Status.SENT,
        )
        self.order_item = PurchaseOrderItem.objects.create(
            purchase_order=self.order,
            ingredient=self.ingredient,
            quantity=Decimal("100"),
            unit_price=Decimal("10.00"),
        )
        self.invoice = DjangoPurchaseInvoiceRepository().save(PurchaseInvoice(
            id=None,
            business_id=self.business.id,
            supplier_id=self.supplier.id,
            invoice_number="INV-RACE",
            invoice_date=date(2026, 11, 2),
            purchase_order_id=self.order.id,
            items=[PurchaseInvoiceItem(
                ingredient_id=self.ingredient.id,
                purchase_order_item_id=self.order_item.id,
                quantity=Decimal("10"),
                unit_price=Decimal("10.00"),
            )],
        ))

    def test_approval_lock_prevents_draft_edit_from_slipping_between_read_and_transition(self):
        barrier = Barrier(2)

        class BarrierRepository(DjangoPurchaseInvoiceRepository):
            def lock_for_approval(inner_self, business_id, invoice_id):
                locked = super(BarrierRepository, inner_self).lock_for_approval(
                    business_id, invoice_id,
                )
                if locked:
                    barrier.wait(timeout=15)
                return locked

        def approve():
            connections.close_all()
            try:
                return ApprovePurchaseInvoiceUseCase(
                    BarrierRepository(), DjangoTransactionManager(),
                ).execute(ApprovePurchaseInvoiceDTO(
                    business_id=self.business.id,
                    purchase_invoice_id=self.invoice.id,
                    approved_by_id=self.user.id,
                    approved_at=datetime(2026, 11, 3, 12),
                ))
            except Exception as error:
                return error
            finally:
                connections.close_all()

        def edit():
            connections.close_all()
            try:
                barrier.wait(timeout=15)
                repository = DjangoPurchaseInvoiceRepository()
                candidate = repository.get_by_id_for_business(
                    self.invoice.id, self.business.id,
                )
                candidate.items[0].unit_price = Decimal("99.00")
                return repository.save(candidate)
            except Exception as error:
                return error
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            approval_future = executor.submit(approve)
            edit_future = executor.submit(edit)
            approval_result = approval_future.result(timeout=30)
            edit_result = edit_future.result(timeout=30)

        self.assertEqual(approval_result.status, PurchaseInvoiceStatus.APPROVED)
        self.assertIsInstance(edit_result, ValueError)
        self.assertIn("Only draft", str(edit_result))
        stored = DjangoPurchaseInvoiceRepository().get_by_id_for_business(
            self.invoice.id, self.business.id,
        )
        self.assertEqual(stored.status, PurchaseInvoiceStatus.APPROVED)
        self.assertEqual(stored.items[0].unit_price, Decimal("10.00"))
