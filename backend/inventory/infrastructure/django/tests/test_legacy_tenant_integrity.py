from decimal import Decimal
from unittest import skipUnless

from django.db import IntegrityError, connection, transaction
from django.test import TestCase

from accounts.models import Business
from inventory.infrastructure.django.models import (
    InventoryOperation,
    InventoryOperationLine,
    InventoryReservation,
    InventoryReservationLine,
    InventoryV1Stock,
    InventoryV1StockMovement,
)
from inventory.models import (
    CompoundMaterialComponent,
    Ingredient,
    Recipe,
    RecipeInput,
    RecipeOutput,
    Stock,
    Warehouse,
)


@skipUnless(connection.vendor == "postgresql", "Tenant integrity triggers are PostgreSQL-only")
class InventoryLegacyTenantIntegrityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.business = Business.objects.create(name="Tenant A", slug="tenant-a-integrity")
        cls.other_business = Business.objects.create(name="Tenant B", slug="tenant-b-integrity")
        cls.warehouse = Warehouse.objects.create(
            business=cls.business, name="A warehouse", is_default=True
        )
        cls.other_warehouse = Warehouse.objects.create(
            business=cls.other_business, name="B warehouse", is_default=True
        )
        cls.raw = Ingredient.objects.create(
            business=cls.business, name="A raw", unit="kg", preparation_level="raw"
        )
        cls.other_raw = Ingredient.objects.create(
            business=cls.other_business, name="B raw", unit="kg", preparation_level="raw"
        )
        cls.compound = Ingredient.objects.create(
            business=cls.business, name="A compound", unit="kg", preparation_level="semi_prepared"
        )
        cls.recipe = Recipe.objects.create(business=cls.business, name="A recipe")

    def test_legacy_stock_rejects_cross_business_references(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Stock.objects.create(
                    warehouse=self.warehouse, ingredient=self.other_raw
                )

    def test_compound_components_require_same_business_and_expected_levels(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CompoundMaterialComponent.objects.create(
                    compound=self.compound,
                    ingredient=self.other_raw,
                    quantity=Decimal("1"),
                    unit="kg",
                )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CompoundMaterialComponent.objects.create(
                    compound=self.raw,
                    ingredient=self.raw,
                    quantity=Decimal("1"),
                    unit="kg",
                )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CompoundMaterialComponent.objects.create(
                    compound=self.compound,
                    ingredient=self.compound,
                    quantity=Decimal("1"),
                    unit="kg",
                )

    def test_recipe_input_and_output_require_same_business(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                RecipeInput.objects.create(
                    recipe=self.recipe, ingredient=self.other_raw,
                    quantity=Decimal("1"), unit="kg",
                )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                RecipeOutput.objects.create(
                    recipe=self.recipe, ingredient=self.other_raw,
                    quantity=Decimal("1"), unit="kg",
                )

    def test_parent_business_changes_cannot_invalidate_legacy_stock(self):
        Stock.objects.create(warehouse=self.warehouse, ingredient=self.raw)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Ingredient.objects.filter(pk=self.raw.pk).update(
                    business_id=self.other_business.pk
                )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Warehouse.objects.filter(pk=self.warehouse.pk).update(
                    business_id=self.other_business.pk
                )

    def test_parent_business_and_preparation_changes_cannot_invalidate_composition(self):
        CompoundMaterialComponent.objects.create(
            compound=self.compound, ingredient=self.raw,
            quantity=Decimal("1"), unit="kg",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Ingredient.objects.filter(pk=self.compound.pk).update(
                    business_id=self.other_business.pk
                )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Ingredient.objects.filter(pk=self.raw.pk).update(
                    preparation_level="semi_prepared"
                )

    def test_recipe_business_change_cannot_invalidate_recipe_lines(self):
        RecipeInput.objects.create(
            recipe=self.recipe, ingredient=self.raw,
            quantity=Decimal("1"), unit="kg",
        )
        RecipeOutput.objects.create(
            recipe=self.recipe, ingredient=self.compound,
            quantity=Decimal("1"), unit="kg", is_primary=True,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Recipe.objects.filter(pk=self.recipe.pk).update(
                    business_id=self.other_business.pk
                )

    def test_parent_business_changes_cannot_invalidate_v1_stock_movements(self):
        stock = InventoryV1Stock.objects.create(
            business=self.business,
            warehouse=self.warehouse,
            ingredient=self.raw,
            unit="kg",
        )
        InventoryV1StockMovement.objects.create(
            business=self.business,
            stock=stock,
            movement_type="receipt",
            direction="in",
            quantity=Decimal("1"),
            unit="kg",
            unit_cost=Decimal("1"),
            balance_after=Decimal("1"),
            average_cost_before=Decimal("0"),
            source_type="tenant-integrity-test",
            source_document_id=1,
            source_line_id=1,
            operation_kind="receive",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryV1Stock.objects.filter(pk=stock.pk).update(
                    business=self.other_business,
                    warehouse=self.other_warehouse,
                    ingredient=self.other_raw,
                )

    def test_operation_business_and_warehouse_change_cannot_invalidate_lines(self):
        operation = InventoryOperation.objects.create(
            business=self.business,
            operation_type=InventoryOperation.Type.ISSUE,
            status=InventoryOperation.Status.DRAFT,
            warehouse=self.warehouse,
            created_by_id=1,
        )
        InventoryOperationLine.objects.create(
            operation=operation,
            ingredient=self.raw,
            quantity=Decimal("1"),
            unit="kg",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryOperation.objects.filter(pk=operation.pk).update(
                    business=self.other_business,
                    warehouse=self.other_warehouse,
                )

    def test_reservation_business_and_warehouse_change_cannot_invalidate_lines(self):
        from uuid import uuid4

        reservation = InventoryReservation.objects.create(
            business=self.business,
            warehouse=self.warehouse,
            source_type="manual",
            source_id=None,
            reason="Tenant integrity test",
            status=InventoryReservation.Status.ACTIVE,
            idempotency_key=uuid4(),
            payload_fingerprint="a" * 64,
            created_by_id=1,
        )
        InventoryReservationLine.objects.create(
            reservation=reservation,
            ingredient=self.raw,
            quantity=Decimal("1"),
            unit="kg",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryReservation.objects.filter(pk=reservation.pk).update(
                    business=self.other_business,
                    warehouse=self.other_warehouse,
                )


    def test_v1_stock_movement_rejects_foreign_business(self):
        stock = InventoryV1Stock.objects.create(
            business=self.business,
            warehouse=self.warehouse,
            ingredient=self.raw,
            unit="kg",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryV1StockMovement.objects.create(
                    business=self.other_business,
                    stock=stock,
                    movement_type="receipt",
                    direction="in",
                    quantity=Decimal("1"),
                    unit="kg",
                    unit_cost=Decimal("1"),
                    balance_after=Decimal("1"),
                    average_cost_before=Decimal("0"),
                    source_type="foreign-tenant-test",
                    source_document_id=101,
                    source_line_id=101,
                    operation_kind="receive",
                )

    def test_v1_operation_line_rejects_foreign_ingredient(self):
        operation = InventoryOperation.objects.create(
            business=self.business,
            operation_type=InventoryOperation.Type.ISSUE,
            status=InventoryOperation.Status.DRAFT,
            warehouse=self.warehouse,
            created_by_id=1,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryOperationLine.objects.create(
                    operation=operation,
                    ingredient=self.other_raw,
                    quantity=Decimal("1"),
                    unit="kg",
                )

    def test_v1_reservation_line_rejects_foreign_ingredient(self):
        from uuid import uuid4

        reservation = InventoryReservation.objects.create(
            business=self.business,
            warehouse=self.warehouse,
            source_type="manual",
            source_id=None,
            reason="Tenant integrity test",
            status=InventoryReservation.Status.ACTIVE,
            idempotency_key=uuid4(),
            payload_fingerprint="b" * 64,
            created_by_id=1,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryReservationLine.objects.create(
                    reservation=reservation,
                    ingredient=self.other_raw,
                    quantity=Decimal("1"),
                    unit="kg",
                )

    def test_warehouse_business_change_cannot_invalidate_v1_records(self):
        InventoryV1Stock.objects.create(
            business=self.business,
            warehouse=self.warehouse,
            ingredient=self.raw,
            unit="kg",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Warehouse.objects.filter(pk=self.warehouse.pk).update(
                    business_id=self.other_business.pk
                )

        operation_warehouse = Warehouse.objects.create(
            business=self.business, name="Operation warehouse"
        )
        InventoryOperation.objects.create(
            business=self.business,
            operation_type=InventoryOperation.Type.ISSUE,
            status=InventoryOperation.Status.DRAFT,
            warehouse=operation_warehouse,
            created_by_id=1,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Warehouse.objects.filter(pk=operation_warehouse.pk).update(
                    business_id=self.other_business.pk
                )

        from uuid import uuid4

        reservation_warehouse = Warehouse.objects.create(
            business=self.business, name="Reservation warehouse"
        )
        InventoryReservation.objects.create(
            business=self.business,
            warehouse=reservation_warehouse,
            source_type="manual",
            source_id=None,
            reason="Tenant integrity test",
            status=InventoryReservation.Status.ACTIVE,
            idempotency_key=uuid4(),
            payload_fingerprint="c" * 64,
            created_by_id=1,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Warehouse.objects.filter(pk=reservation_warehouse.pk).update(
                    business_id=self.other_business.pk
                )

    def test_ingredient_business_change_cannot_invalidate_v1_records(self):
        InventoryV1Stock.objects.create(
            business=self.business,
            warehouse=self.warehouse,
            ingredient=self.raw,
            unit="kg",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Ingredient.objects.filter(pk=self.raw.pk).update(
                    business_id=self.other_business.pk
                )

        operation = InventoryOperation.objects.create(
            business=self.business,
            operation_type=InventoryOperation.Type.ISSUE,
            status=InventoryOperation.Status.DRAFT,
            warehouse=self.warehouse,
            created_by_id=1,
        )
        InventoryOperationLine.objects.create(
            operation=operation,
            ingredient=self.raw,
            quantity=Decimal("1"),
            unit="kg",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Ingredient.objects.filter(pk=self.raw.pk).update(
                    business_id=self.other_business.pk
                )

        from uuid import uuid4

        reservation = InventoryReservation.objects.create(
            business=self.business,
            warehouse=self.warehouse,
            source_type="manual",
            source_id=None,
            reason="Tenant integrity test",
            status=InventoryReservation.Status.ACTIVE,
            idempotency_key=uuid4(),
            payload_fingerprint="d" * 64,
            created_by_id=1,
        )
        InventoryReservationLine.objects.create(
            reservation=reservation,
            ingredient=self.raw,
            quantity=Decimal("1"),
            unit="kg",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Ingredient.objects.filter(pk=self.raw.pk).update(
                    business_id=self.other_business.pk
                )
