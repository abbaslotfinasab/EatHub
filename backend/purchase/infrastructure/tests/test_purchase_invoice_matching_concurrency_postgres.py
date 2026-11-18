from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from decimal import Decimal
from threading import Event
from unittest import skipUnless

from django.db import connection, connections, transaction
from django.test import TransactionTestCase

from accounts.models import Business, User
from inventory.models import Ingredient
from purchase.application.dto.purchase_invoice_posting import PostPurchaseInvoiceDTO
from purchase.application.use_cases.purchase_invoice.match_purchase_invoice import (
    MatchPurchaseInvoiceUseCase,
)
from purchase.application.use_cases.purchase_invoice.post_purchase_invoice import (
    PostPurchaseInvoice,
)
from purchase.domain.entities.purchase_invoice import PurchaseInvoice, PurchaseInvoiceItem
from purchase.infrastructure.persistence.django.repositories.accounts_payable_repository import (
    DjangoAccountsPayableRepository,
)
from purchase.infrastructure.persistence.django.repositories.purchase_invoice_matching_repository import (
    DjangoPurchaseInvoiceMatchingRepository,
)
from purchase.infrastructure.persistence.django.repositories.purchase_invoice_repository import (
    DjangoPurchaseInvoiceRepository,
)
from purchase.infrastructure.persistence.transaction import DjangoTransactionManager
from purchase.models import (
    AccountsPayable,
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseInvoice as DjangoPurchaseInvoice,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
)


@skipUnless(connection.vendor == "postgresql", "Invoice matching race verification requires PostgreSQL.")
class PurchaseInvoiceMatchingConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.business = Business.objects.create(name="Invoice matching race")
        self.user = User.objects.create_user(
            email="invoice-matching-race@example.com",
            password="test-only",
            name="Invoice Matching",
        )
        self.supplier = Supplier.objects.create(
            business=self.business,
            name="Supplier",
        )
        self.ingredient = Ingredient.objects.create(
            business=self.business,
            name="Flour",
            unit=Ingredient.Unit.KG,
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
        receipt = GoodsReceipt.objects.create(
            business=self.business,
            purchase_order=self.order,
            received_by=self.user,
            received_date=datetime(2026, 11, 2, 12, tzinfo=timezone.utc),
        )
        GoodsReceiptItem.objects.create(
            receipt=receipt,
            purchase_order_item=self.order_item,
            received_quantity=Decimal("5"),
            rejected_quantity=Decimal("0"),
        )

        invoice_repository = DjangoPurchaseInvoiceRepository()
        self.invoice_ids = []
        for index in (1, 2):
            invoice = invoice_repository.save(PurchaseInvoice(
                id=None,
                business_id=self.business.id,
                supplier_id=self.supplier.id,
                invoice_number=f"INV-RACE-{index}",
                invoice_date=date(2026, 11, 3),
                purchase_order_id=self.order.id,
                items=[PurchaseInvoiceItem(
                    ingredient_id=self.ingredient.id,
                    purchase_order_item_id=self.order_item.id,
                    quantity=Decimal("4"),
                    unit_price=Decimal("10.00"),
                )],
            ))
            invoice.approve(
                self.user.id,
                datetime(2026, 11, 4, 12, tzinfo=timezone.utc),
            )
            with transaction.atomic():
                approved = invoice_repository.save_approved(invoice)
            self.invoice_ids.append(approved.id)

    def test_two_invoices_cannot_consume_the_same_received_quantity_concurrently(self):
        first_context_loaded = Event()
        second_lock_attempted = Event()
        second_context_loaded = Event()
        release_first = Event()
        first_invoice_id, second_invoice_id = self.invoice_ids

        class CoordinatedMatchingRepository(DjangoPurchaseInvoiceMatchingRepository):
            def lock_invoice_for_matching(inner_self, business_id, invoice_id):
                if invoice_id == second_invoice_id:
                    second_lock_attempted.set()
                return super().lock_invoice_for_matching(business_id, invoice_id)

            def load_matching_context(inner_self, business_id, invoice_id):
                context = super().load_matching_context(business_id, invoice_id)
                if invoice_id == first_invoice_id:
                    first_context_loaded.set()
                    if not release_first.wait(timeout=20):
                        raise TimeoutError("Timed out waiting to release the first invoice match.")
                elif invoice_id == second_invoice_id:
                    second_context_loaded.set()
                return context

        def post_invoice(invoice_id):
            connections.close_all()
            try:
                transaction_manager = DjangoTransactionManager()
                matcher = MatchPurchaseInvoiceUseCase(
                    CoordinatedMatchingRepository(),
                    transaction_manager,
                )
                use_case = PostPurchaseInvoice(
                    DjangoPurchaseInvoiceRepository(),
                    DjangoAccountsPayableRepository(),
                    matcher,
                    transaction_manager,
                )
                return use_case.execute(PostPurchaseInvoiceDTO(
                    business_id=self.business.id,
                    purchase_invoice_id=invoice_id,
                    posted_by_id=self.user.id,
                    posted_at=datetime(2026, 11, 5, 12, tzinfo=timezone.utc),
                    due_date=date(2026, 12, 5),
                ))
            except Exception as error:
                return error
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            first_future = executor.submit(post_invoice, first_invoice_id)
            self.assertTrue(first_context_loaded.wait(timeout=15))
            second_future = executor.submit(post_invoice, second_invoice_id)
            try:
                self.assertTrue(second_lock_attempted.wait(timeout=15))
                # The second transaction must wait on the shared PO line lock,
                # rather than reading the same pre-posting invoice aggregate.
                self.assertFalse(second_context_loaded.wait(timeout=0.5))
            finally:
                release_first.set()

            first_result = first_future.result(timeout=30)
            second_result = second_future.result(timeout=30)

        self.assertFalse(
            isinstance(first_result, Exception),
            f"first={first_result!r}; second={second_result!r}",
        )
        self.assertIsInstance(second_result, ValueError)
        self.assertIn("current MATCHED", str(second_result))
        self.assertEqual(
            DjangoPurchaseInvoice.objects.filter(
                id__in=self.invoice_ids,
                status=DjangoPurchaseInvoice.Status.POSTED,
            ).count(),
            1,
        )
        self.assertEqual(
            AccountsPayable.objects.filter(
                business=self.business,
                source_invoice_id__in=self.invoice_ids,
            ).count(),
            1,
        )
