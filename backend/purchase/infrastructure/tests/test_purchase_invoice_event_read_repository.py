from datetime import date
from decimal import Decimal

from django.test import TestCase

from accounts.models import Business, User
from inventory.models import Ingredient
from purchase.domain.entities.purchase_invoice import PurchaseInvoice, PurchaseInvoiceItem
from purchase.infrastructure.persistence.django.repositories.purchase_invoice_repository import (
    DjangoPurchaseInvoiceRepository,
)
from purchase.infrastructure.persistence.django.repositories.purchase_invoice_event_read_repository import (
    DjangoPurchaseInvoiceEventReadRepository,
)
from purchase.models import PurchaseInvoiceEvent, PurchaseOrder, PurchaseOrderItem, Supplier


class PurchaseInvoiceEventReadRepositoryTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Invoice Event Business")
        self.supplier = Supplier.objects.create(business=self.business, name="Supplier")
        self.ingredient = Ingredient.objects.create(
            business=self.business, name="Flour", unit=Ingredient.Unit.KG,
        )
        self.user = User.objects.create_user(
            email="invoice-events@example.com",
            password="password",
            name="Invoice Events",
            number="9191",
        )
        order = PurchaseOrder.objects.create(
            business=self.business,
            supplier=self.supplier,
            order_date=date(2026, 9, 1),
            status=PurchaseOrder.Status.SENT,
        )
        order_item = PurchaseOrderItem.objects.create(
            purchase_order=order,
            ingredient=self.ingredient,
            quantity=Decimal("10.000"),
            unit_price=Decimal("10.00"),
        )
        invoice = DjangoPurchaseInvoiceRepository().save(PurchaseInvoice(
            id=None,
            business_id=self.business.id,
            supplier_id=self.supplier.id,
            invoice_number="EVENT-1",
            invoice_date=date(2026, 9, 10),
            purchase_order_id=order.id,
            items=[PurchaseInvoiceItem(
                ingredient_id=self.ingredient.id,
                quantity=Decimal("1.000"),
                unit_price=Decimal("10.00"),
                purchase_order_item_id=order_item.id,
            )],
        ))
        self.invoice_id = invoice.id
        self.repository = DjangoPurchaseInvoiceEventReadRepository()

    def create_event(self, event_type):
        return PurchaseInvoiceEvent.objects.create(
            business_id=self.business.id,
            purchase_invoice_id=self.invoice_id,
            actor=self.user,
            event_type=event_type,
            previous_status=None,
            resulting_status="draft",
            metadata={"event": event_type},
        )

    def test_list_is_tenant_scoped_and_preserves_order_and_actor(self):
        first = self.create_event(PurchaseInvoiceEvent.EventType.CREATED)
        second = self.create_event(PurchaseInvoiceEvent.EventType.UPDATED)

        with self.assertNumQueries(1):
            events = self.repository.list_for_invoice(
                business_id=self.business.id,
                purchase_invoice_id=self.invoice_id,
            )

        self.assertEqual([event.id for event in events], [first.id, second.id])
        self.assertEqual([event.actor_name for event in events], ["Invoice Events", "Invoice Events"])
        self.assertEqual([event.event_type for event in events], ["created", "updated"])

    def test_foreign_business_cannot_read_invoice_events(self):
        self.create_event(PurchaseInvoiceEvent.EventType.CREATED)
        other_business = Business.objects.create(name="Other Invoice Event Business")

        events = self.repository.list_for_invoice(
            business_id=other_business.id,
            purchase_invoice_id=self.invoice_id,
        )

        self.assertEqual(events, [])
