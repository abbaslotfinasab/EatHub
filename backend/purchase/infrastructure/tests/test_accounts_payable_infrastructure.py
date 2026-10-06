from datetime import date
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import Business, User
from purchase.domain.entities.accounts_payable import AccountsPayable
from purchase.domain.enums.accounts_payable_status import AccountsPayableStatus
from purchase.infrastructure.persistence.django.repositories.accounts_payable_repository import (
    DjangoAccountsPayableRepository,
)
from purchase.models import (
    AccountsPayable as DjangoAccountsPayable,
    PurchaseInvoice,
    Supplier,
)


class AccountsPayableInfrastructureTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="AP Business")
        self.other_business = Business.objects.create(name="Other AP Business")
        self.supplier = Supplier.objects.create(business=self.business, name="Supplier")
        self.other_supplier = Supplier.objects.create(business=self.other_business, name="Other")
        self.user = User.objects.create_user(
            email="ap@example.com", password="password", name="AP", number="9201",
        )
        self.invoice = PurchaseInvoice.objects.create(
            business=self.business,
            supplier=self.supplier,
            invoice_number="AP-INV-1",
            invoice_date=date(2026, 10, 1),
            subtotal=Decimal("100.00"),
            total_price=Decimal("125.50"),
        )
        self.other_invoice = PurchaseInvoice.objects.create(
            business=self.other_business,
            supplier=self.other_supplier,
            invoice_number="AP-INV-2",
            invoice_date=date(2026, 10, 1),
            subtotal=Decimal("50.00"),
            total_price=Decimal("50.00"),
        )
        self.repository = DjangoAccountsPayableRepository()

    def payable(self, **overrides):
        values = {
            "id": None,
            "business_id": self.business.id,
            "supplier_id": self.supplier.id,
            "source_invoice_id": self.invoice.id,
            "amount": Decimal("125.50"),
            "due_date": date(2026, 11, 1),
            "status": AccountsPayableStatus.OPEN,
        }
        values.update(overrides)
        return AccountsPayable(**values)

    def test_get_by_id_and_source_invoice_are_business_scoped(self):
        saved = self.repository.create(self.payable())
        self.assertEqual(
            self.repository.get_by_id_for_business(saved.id, self.business.id).id,
            saved.id,
        )
        self.assertIsNone(self.repository.get_by_id_for_business(saved.id, self.other_business.id))
        self.assertEqual(
            self.repository.get_by_source_invoice_id(self.invoice.id, self.business.id).id,
            saved.id,
        )
        self.assertIsNone(
            self.repository.get_by_source_invoice_id(self.invoice.id, self.other_business.id),
        )

    def test_list_is_business_scoped(self):
        self.repository.create(self.payable())
        other = AccountsPayable(
            id=None,
            business_id=self.other_business.id,
            supplier_id=self.other_supplier.id,
            source_invoice_id=self.other_invoice.id,
            amount=Decimal("50.00"),
        )
        self.repository.create(other)
        self.assertEqual(
            [row.source_invoice_id for row in self.repository.list(self.business.id)],
            [self.invoice.id],
        )

    def test_duplicate_source_invoice_is_prevented(self):
        self.repository.create(self.payable())
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.repository.create(self.payable())
        self.assertTrue(self.repository.exists_for_source_invoice(self.invoice.id, self.business.id))

    def test_supplier_and_source_invoice_business_ownership_is_enforced(self):
        with self.assertRaisesRegex(ValueError, "does not exist in this business"):
            self.repository.create(self.payable(source_invoice_id=self.other_invoice.id))
        with self.assertRaisesRegex(ValueError, "does not match"):
            self.repository.create(self.payable(supplier_id=self.other_supplier.id))

    def test_database_rejects_nonpositive_amount(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                DjangoAccountsPayable.objects.create(
                    business=self.business,
                    supplier=self.supplier,
                    source_invoice=self.invoice,
                    amount=Decimal("0"),
                )

    def test_source_invoice_relation_is_unique(self):
        self.assertTrue(DjangoAccountsPayable._meta.get_field("source_invoice").unique)

    def test_repository_creation_checks_supplier_and_invoice_business(self):
        with self.assertRaisesRegex(ValueError, "does not exist in this business"):
            self.repository.create(self.payable(business_id=self.other_business.id))
