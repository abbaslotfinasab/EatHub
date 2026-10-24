from datetime import datetime
from decimal import Decimal
import inspect
from unittest.mock import patch
from uuid import uuid4

from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import Business, User
from inventory.models import Ingredient, Warehouse
from purchase.domain.entities.goods_receipt import GoodsReceipt, GoodsReceiptItem
from purchase.infrastructure.persistence.django.mappers import GoodsReceiptMapper
from purchase.infrastructure.persistence.django.repositories.goods_receipt_repository import (
    DjangoGoodsReceiptRepository,
)
from purchase.infrastructure.persistence.django.repositories.purchase_order_line_reader import (
    DjangoPurchaseOrderLineReader,
)
from purchase.infrastructure.persistence.django.repositories.purchase_order_repository import (
    DjangoPurchaseOrderRepository,
)
from purchase.models import (
    GoodsReceipt as DjangoGoodsReceipt,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
)


class GoodsReceiptInfrastructureTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.business = Business.objects.create(name="Business", slug="business")
        cls.other_business = Business.objects.create(
            name="Other Business",
            slug="other-business",
        )
        cls.user = User.objects.create_user(
            email="receiver@example.com",
            password="password",
            name="Receiver",
        )
        cls.ingredient = Ingredient.objects.create(
            business=cls.business,
            name="Flour",
            unit=Ingredient.Unit.KG,
        )
        cls.other_ingredient = Ingredient.objects.create(
            business=cls.other_business,
            name="Other Flour",
            unit=Ingredient.Unit.KG,
        )
        cls.warehouse = Warehouse.objects.create(
            business=cls.business,
            name="Main",
            is_default=True,
        )
        cls.supplier = Supplier.objects.create(
            business=cls.business,
            name="Supplier",
        )
        cls.purchase_order = PurchaseOrder.objects.create(
            business=cls.business,
            supplier=cls.supplier,
            order_date=datetime(2026, 9, 8).date(),
            status=PurchaseOrder.Status.SENT,
        )
        cls.purchase_order_item = PurchaseOrderItem.objects.create(
            purchase_order=cls.purchase_order,
            ingredient=cls.ingredient,
            quantity=Decimal("10"),
            unit_price=Decimal("500.00"),
            purchase_unit="kg",
        )

    def receipt(self, quantity="4", rejected="0"):
        return GoodsReceipt(
            id=None,
            business_id=self.business.id,
            purchase_order_id=self.purchase_order.id,
            received_by_id=self.user.id,
            received_date=datetime(2026, 9, 8, 12),
            idempotency_key=uuid4(),
            payload_fingerprint="a" * 64,
            payload_version=1,
            items=[GoodsReceiptItem(
                self.purchase_order_item.id,
                Decimal(quantity),
                Decimal(rejected),
            )],
        )

    def test_repository_persists_and_loads_scoped_aggregate(self):
        repository = DjangoGoodsReceiptRepository()
        saved = repository.save(self.receipt())

        loaded = repository.get_by_id_for_business(
            saved.id,
            self.business.id,
        )

        self.assertEqual(loaded.business_id, self.business.id)
        self.assertEqual(loaded.items[0].received_quantity, Decimal("4"))
        self.assertIsNotNone(loaded.items[0].id)
        self.assertIsNone(
            repository.get_by_id_for_business(saved.id, self.other_business.id)
        )

    def test_repository_preserves_legacy_receipts_without_idempotency_values(self):
        saved = DjangoGoodsReceipt.objects.create(
            business=self.business,
            purchase_order=self.purchase_order,
            received_by=self.user,
            received_date=datetime(2026, 9, 8, 12),
        )

        self.assertIsNone(saved.idempotency_key)
        self.assertIsNone(saved.payload_fingerprint)
        self.assertIsNone(saved.payload_version)
        DjangoGoodsReceipt.objects.create(
            business=self.business,
            purchase_order=self.purchase_order,
            received_by=self.user,
            received_date=datetime(2026, 9, 8, 12),
        )
        self.assertIsNone(
            DjangoGoodsReceiptRepository().get_by_idempotency_key_for_business(
                uuid4(), self.business.id
            )
        )

    def test_idempotency_key_is_unique_per_business_and_fingerprint_round_trips(self):
        repository = DjangoGoodsReceiptRepository()
        key = uuid4()
        fingerprint = "a" * 64
        first = self.receipt()
        first.idempotency_key = key
        first.payload_fingerprint = fingerprint
        first.payload_version = 1
        saved = repository.save(first)

        loaded = repository.get_by_idempotency_key_for_business(
            key,
            self.business.id,
        )

        self.assertEqual(loaded.id, saved.id)
        self.assertEqual(loaded.payload_fingerprint, fingerprint)
        self.assertEqual(loaded.payload_version, 1)
        duplicate = self.receipt()
        duplicate.idempotency_key = key
        duplicate.payload_fingerprint = "b" * 64
        duplicate.payload_version = 1
        duplicate_model = GoodsReceiptMapper.to_model(duplicate)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                duplicate_model.save(force_insert=True)

    def test_idempotency_key_and_fingerprint_must_be_set_together(self):
        invalid_values = [
            (uuid4(), None, None),
            (uuid4(), "e" * 64, None),
            (None, "e" * 64, 1),
        ]
        for key, fingerprint, version in invalid_values:
            with self.subTest(key=key, fingerprint=fingerprint, version=version):
                receipt = self.receipt()
                receipt.idempotency_key = key
                receipt.payload_fingerprint = fingerprint
                receipt.payload_version = version
                model = GoodsReceiptMapper.to_model(receipt)
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        model.save(force_insert=True)

    def test_unrelated_header_integrity_error_is_not_translated_to_key_race(self):
        receipt = self.receipt()
        error = IntegrityError("unrelated header constraint")

        with patch.object(DjangoGoodsReceipt, "save", side_effect=error) as save_header:
            with self.assertRaises(IntegrityError) as raised:
                DjangoGoodsReceiptRepository().save(receipt)

        self.assertIs(raised.exception, error)
        save_header.assert_called_once_with(force_insert=True)

    def test_same_idempotency_key_is_independent_across_businesses(self):
        key = uuid4()
        fingerprint = "c" * 64
        own_receipt = self.receipt()
        own_receipt.idempotency_key = key
        own_receipt.payload_fingerprint = fingerprint
        own_receipt.payload_version = 1
        own_saved = DjangoGoodsReceiptRepository().save(own_receipt)
        other_supplier = Supplier.objects.create(
            business=self.other_business,
            name="Other Supplier",
        )
        other_order = PurchaseOrder.objects.create(
            business=self.other_business,
            supplier=other_supplier,
            order_date=datetime(2026, 9, 8).date(),
            status=PurchaseOrder.Status.SENT,
        )
        other_item = PurchaseOrderItem.objects.create(
            purchase_order=other_order,
            ingredient=self.other_ingredient,
            quantity=Decimal("10"),
            unit_price=Decimal("4"),
            purchase_unit="kg",
        )
        other_receipt = GoodsReceipt(
            id=None,
            business_id=self.other_business.id,
            purchase_order_id=other_order.id,
            received_by_id=self.user.id,
            received_date=datetime(2026, 9, 8, 12),
            idempotency_key=key,
            payload_fingerprint=fingerprint,
            payload_version=1,
            items=[GoodsReceiptItem(other_item.id, Decimal("1"))],
        )

        saved = DjangoGoodsReceiptRepository().save(other_receipt)

        self.assertEqual(saved.business_id, self.other_business.id)
        self.assertEqual(own_saved.business_id, self.business.id)
        self.assertEqual(
            DjangoGoodsReceiptRepository().get_by_idempotency_key_for_business(
                key, self.business.id
            ).id,
            own_saved.id,
        )

    def test_for_update_loader_locks_only_tenant_scoped_po_root(self):
        repository = DjangoPurchaseOrderRepository()
        source = inspect.getsource(
            DjangoPurchaseOrderRepository.get_by_id_for_business_for_update
        )
        self.assertIn('select_for_update(of=("self",))', source)
        self.assertIn("business_id=business_id", source)
        self.assertLess(source.index("select_for_update"), source.index("self._aggregate_queryset()"))

        with transaction.atomic():
            locked = repository.get_by_id_for_business_for_update(
                self.purchase_order.id,
                self.business.id,
            )
            self.assertEqual(locked.id, self.purchase_order.id)
            self.assertIsNone(repository.get_by_id_for_business_for_update(
                self.purchase_order.id,
                self.other_business.id,
            ))

    def test_existing_goods_receipt_cannot_be_updated(self):
        repository = DjangoGoodsReceiptRepository()
        saved = repository.save(self.receipt())
        saved.items[0].received_quantity = Decimal("5")
        with self.assertRaisesRegex(ValueError, "immutable"):
            repository.save(saved)

    def test_received_quantity_query_excludes_rejected_quantity(self):
        repository = DjangoGoodsReceiptRepository()
        repository.save(self.receipt(quantity="4", rejected="3"))

        quantities = repository.received_quantities_for_purchase_order(
            self.business.id,
            self.purchase_order.id,
        )

        self.assertEqual(
            quantities[self.purchase_order_item.id],
            Decimal("4"),
        )

    def test_line_reader_is_scoped_to_order_and_business(self):
        lines = DjangoPurchaseOrderLineReader().get_lines(
            self.purchase_order.id,
            self.business.id,
        )

        self.assertEqual(
            lines[self.purchase_order_item.id].ingredient_id,
            self.ingredient.id,
        )
        self.assertEqual(
            lines[self.purchase_order_item.id].ordered_quantity,
            Decimal("10"),
        )
        self.assertEqual(lines[self.purchase_order_item.id].purchase_unit.value, "kg")
        self.assertEqual(
            DjangoPurchaseOrderLineReader().get_lines(
                self.purchase_order.id,
                self.other_business.id,
            ),
            {},
        )

    def test_mapper_maps_the_full_aggregate(self):
        model = DjangoGoodsReceipt(
            business=self.business,
            purchase_order=self.purchase_order,
            received_by=self.user,
            received_date=datetime(2026, 9, 8, 12),
            notes="note",
        )
        model.save()
        model.items.create(
            purchase_order_item=self.purchase_order_item,
            received_quantity=Decimal("4"),
            rejected_quantity=Decimal("1"),
            purchase_unit="kg",
        )

        entity = GoodsReceiptMapper.to_domain(model)

        self.assertEqual(entity.notes, "note")
        self.assertEqual(entity.total_received_quantity, Decimal("4"))
        self.assertEqual(entity.total_rejected_quantity, Decimal("1"))
        self.assertIsNotNone(entity.items[0].id)
        self.assertEqual(entity.items[0].purchase_unit.value, "kg")
