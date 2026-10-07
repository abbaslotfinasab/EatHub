import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest


MIGRATION_PATH = Path(__file__).parents[2] / "migrations" / "0009_paymentallocation_accounts_payable.py"
SPEC = importlib.util.spec_from_file_location("purchase_migration_0009", MIGRATION_PATH)
MIGRATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIGRATION)


class FakeQuerySet:
    def __init__(self, rows, table):
        self.rows = rows
        self.table = table

    def using(self, _database):
        return self

    def all(self):
        return self

    def iterator(self):
        return iter(self.rows)

    def filter(self, **criteria):
        return FakeQuerySet(
            [row for row in self.rows if all(getattr(row, key) == value for key, value in criteria.items())],
            self.table,
        )

    def values(self, *fields):
        return FakeValuesQuerySet([
            {field: getattr(row, field) for field in fields}
            for row in self.rows
        ])

    def first(self):
        return self.rows[0] if self.rows else None

    def update(self, **values):
        for row in self.rows:
            for key, value in values.items():
                setattr(row, key, value)
        return len(self.rows)


class FakeValuesQuerySet:
    def __init__(self, rows):
        self.rows = rows

    def first(self):
        return self.rows[0] if self.rows else None


class FakeManager:
    def __init__(self, rows):
        self.rows = rows

    def using(self, _database):
        return FakeQuerySet(self.rows, self)


class FakeApps:
    def __init__(self, tables):
        self.tables = tables

    def get_model(self, app_label, model_name):
        return SimpleNamespace(objects=FakeManager(self.tables[(app_label, model_name)]))


class PaymentAllocationMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tables = {
            ("purchase", "PaymentAllocation"): [],
            ("purchase", "AccountsPayable"): [],
            ("purchase", "PurchaseInvoice"): [],
            ("purchase", "SupplierPayment"): [],
            ("purchase", "Supplier"): [],
        }
        self.invoice = SimpleNamespace(pk=11, business_id=1, supplier_id=21)
        self.payment = SimpleNamespace(pk=31, business_id=1, supplier_id=21)
        self.payable = SimpleNamespace(id=41, source_invoice_id=11, business_id=1, supplier_id=21)
        self.supplier = SimpleNamespace(pk=21, business_id=1)
        self.tables[("purchase", "PurchaseInvoice")].append(self.invoice)
        self.tables[("purchase", "SupplierPayment")].append(self.payment)
        self.tables[("purchase", "AccountsPayable")].append(self.payable)
        self.tables[("purchase", "Supplier")].append(self.supplier)
        self.allocation = SimpleNamespace(
            pk=51,
            invoice_id=11,
            payment_id=31,
            amount=25,
            created_at="created",
            accounts_payable_id=None,
            business_id=None,
            allocated_at=None,
        )
        self.tables[("purchase", "PaymentAllocation")].append(self.allocation)
        self.apps = FakeApps(self.tables)
        self.schema_editor = SimpleNamespace(connection=SimpleNamespace(alias="default"))

    def run_migration(self):
        MIGRATION.map_legacy_allocations(self.apps, self.schema_editor)

    def assert_fails_without_mapping(self, expected_message):
        with self.assertRaisesRegex(RuntimeError, expected_message):
            self.run_migration()
        for allocation in self.tables[("purchase", "PaymentAllocation")]:
            self.assertIsNone(allocation.accounts_payable_id)
            self.assertIsNone(allocation.business_id)
            self.assertIsNone(allocation.allocated_at)

    def test_valid_legacy_allocation_maps_without_changing_financial_history(self):
        self.run_migration()
        self.assertEqual(self.allocation.accounts_payable_id, self.payable.id)
        self.assertEqual(self.allocation.business_id, self.payment.business_id)
        self.assertEqual(self.allocation.allocated_at, self.allocation.created_at)
        self.assertEqual(self.allocation.amount, 25)
        self.assertEqual(self.allocation.invoice_id, self.invoice.pk)
        self.assertEqual(self.allocation.payment_id, self.payment.pk)

    def test_migration_is_atomic(self):
        self.assertTrue(MIGRATION.Migration.atomic)

    def test_invoice_payable_business_mismatch_fails(self):
        self.payable.business_id = 2
        self.assert_fails_without_mapping("ownership do not match")

    def test_invoice_payment_business_mismatch_fails(self):
        self.payment.business_id = 2
        self.assert_fails_without_mapping("ownership do not match")

    def test_payable_payment_business_mismatch_fails(self):
        self.payable.business_id = 2
        self.assert_fails_without_mapping("ownership do not match")

    def test_invoice_payable_supplier_mismatch_fails(self):
        self.payable.supplier_id = 22
        self.assert_fails_without_mapping("ownership do not match")

    def test_invoice_payment_supplier_mismatch_fails(self):
        self.payment.supplier_id = 22
        self.assert_fails_without_mapping("ownership do not match")

    def test_payable_payment_supplier_mismatch_fails(self):
        self.payable.supplier_id = 22
        self.assert_fails_without_mapping("ownership do not match")

    def test_supplier_from_invoice_belongs_to_another_business_fails(self):
        self.supplier.business_id = 2
        self.assert_fails_without_mapping("ownership do not match")

    def test_missing_accounts_payable_fails(self):
        self.tables[("purchase", "AccountsPayable")].clear()
        self.assert_fails_without_mapping("has no AccountsPayable")

    def test_missing_invoice_fails_when_legacy_constraint_does_not_protect_it(self):
        self.tables[("purchase", "PurchaseInvoice")].clear()
        self.assert_fails_without_mapping("source invoice is missing")

    def test_missing_payment_fails_when_legacy_constraint_does_not_protect_it(self):
        self.tables[("purchase", "SupplierPayment")].clear()
        self.assert_fails_without_mapping("supplier payment is missing")

    def test_missing_supplier_fails(self):
        self.tables[("purchase", "Supplier")].clear()
        self.assert_fails_without_mapping("supplier is missing")

    def test_nonpositive_amount_fails(self):
        self.allocation.amount = 0
        self.assert_fails_without_mapping("nonpositive amount")

    def test_later_invalid_row_does_not_partially_map_earlier_rows(self):
        second = SimpleNamespace(
            pk=52,
            invoice_id=11,
            payment_id=31,
            amount=1,
            created_at="created",
            accounts_payable_id=None,
            business_id=None,
            allocated_at=None,
        )
        self.tables[("purchase", "PaymentAllocation")].append(second)
        self.payment.business_id = 2
        self.assert_fails_without_mapping("ownership do not match")


if __name__ == "__main__":
    unittest.main()
