from decimal import Decimal
from unittest import skipUnless
from uuid import uuid4

from django.db import IntegrityError, connection, transaction
from django.test import TestCase

from accounts.models import Business
from inventory.infrastructure.django.models import (
    InventoryOperation,
    InventoryOperationLine,
    InventoryReservation,
    InventoryReservationLine,
    InventoryV1Stock,
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
class InventoryTenantReferenceUpdateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.business = Business.objects.create(name="Tenant A", slug="tenant-a-ref-update")
        cls.other_business = Business.objects.create(name="Tenant B", slug="tenant-b-ref-update")
        cls.warehouse = Warehouse.objects.create(
            business=cls.business, name="A warehouse", is_default=True
        )
        cls.other_warehouse = Warehouse.objects.create(
            business=cls.other_business, name="B warehouse", is_default=True
        )
        cls.ingredient = Ingredient.objects.create(
            business=cls.business, name="A ingredient", unit="kg"
        )
        cls.other_ingredient = Ingredient.objects.create(
            business=cls.other_business, name="B ingredient", unit="kg"
        )

    def create_stock(self, business, warehouse, ingredient):
        return InventoryV1Stock.objects.create(
            business=business, warehouse=warehouse, ingredient=ingredient, unit="kg"
        )

    def create_operation(self, business, warehouse, *, destination=None):
        return InventoryOperation.objects.create(
            business=business,
            operation_type=(
                InventoryOperation.Type.TRANSFER
                if destination is not None
                else InventoryOperation.Type.ISSUE
            ),
            status=InventoryOperation.Status.DRAFT,
            warehouse=warehouse,
            destination_warehouse=destination,
            created_by_id=1,
        )

    def create_reservation(self, business, warehouse):
        return InventoryReservation.objects.create(
            business=business,
            warehouse=warehouse,
            source_type="manual",
            source_id=None,
            reason="Tenant reference update test",
            status=InventoryReservation.Status.ACTIVE,
            idempotency_key=uuid4(),
            payload_fingerprint="e" * 64,
            created_by_id=1,
        )

    def test_v1_stock_rejects_foreign_warehouse_update_without_business_change(self):
        stock = self.create_stock(self.business, self.warehouse, self.ingredient)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryV1Stock.objects.filter(pk=stock.pk).update(
                    warehouse_id=self.other_warehouse.pk
                )

    def test_v1_stock_rejects_foreign_ingredient_update_without_business_change(self):
        stock = self.create_stock(self.business, self.warehouse, self.ingredient)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryV1Stock.objects.filter(pk=stock.pk).update(
                    ingredient_id=self.other_ingredient.pk
                )

    def test_operation_rejects_foreign_source_warehouse_update_without_business_change(self):
        operation = self.create_operation(self.business, self.warehouse)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryOperation.objects.filter(pk=operation.pk).update(
                    warehouse_id=self.other_warehouse.pk
                )

    def test_operation_rejects_foreign_destination_warehouse_update_without_business_change(self):
        operation = self.create_operation(
            self.business, self.warehouse, destination=self.warehouse
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryOperation.objects.filter(pk=operation.pk).update(
                    destination_warehouse_id=self.other_warehouse.pk
                )

    def test_operation_line_rejects_foreign_ingredient_update(self):
        operation = self.create_operation(self.business, self.warehouse)
        line = InventoryOperationLine.objects.create(
            operation=operation,
            ingredient=self.ingredient,
            quantity=Decimal("1"),
            unit="kg",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryOperationLine.objects.filter(pk=line.pk).update(
                    ingredient_id=self.other_ingredient.pk
                )

    def test_operation_line_rejects_foreign_operation_update(self):
        operation = self.create_operation(self.business, self.warehouse)
        other_operation = self.create_operation(
            self.other_business, self.other_warehouse
        )
        line = InventoryOperationLine.objects.create(
            operation=operation,
            ingredient=self.ingredient,
            quantity=Decimal("1"),
            unit="kg",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryOperationLine.objects.filter(pk=line.pk).update(
                    operation_id=other_operation.pk
                )

    def test_reservation_rejects_foreign_warehouse_update_without_business_change(self):
        reservation = self.create_reservation(self.business, self.warehouse)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryReservation.objects.filter(pk=reservation.pk).update(
                    warehouse_id=self.other_warehouse.pk
                )

    def test_reservation_line_rejects_foreign_ingredient_update(self):
        reservation = self.create_reservation(self.business, self.warehouse)
        line = InventoryReservationLine.objects.create(
            reservation=reservation,
            ingredient=self.ingredient,
            quantity=Decimal("1"),
            unit="kg",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryReservationLine.objects.filter(pk=line.pk).update(
                    ingredient_id=self.other_ingredient.pk
                )

    def test_reservation_line_rejects_foreign_reservation_update(self):
        reservation = self.create_reservation(self.business, self.warehouse)
        other_reservation = self.create_reservation(
            self.other_business, self.other_warehouse
        )
        line = InventoryReservationLine.objects.create(
            reservation=reservation,
            ingredient=self.ingredient,
            quantity=Decimal("1"),
            unit="kg",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryReservationLine.objects.filter(pk=line.pk).update(
                    reservation_id=other_reservation.pk
                )



@skipUnless(connection.vendor == "postgresql", "Tenant integrity triggers are PostgreSQL-only")
class InventoryLegacyTenantReferenceUpdateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.business = Business.objects.create(name="Legacy Tenant A", slug="legacy-tenant-a-ref-update")
        cls.other_business = Business.objects.create(name="Legacy Tenant B", slug="legacy-tenant-b-ref-update")
        cls.warehouse = Warehouse.objects.create(business=cls.business, name="Legacy A warehouse")
        cls.other_warehouse = Warehouse.objects.create(
            business=cls.other_business, name="Legacy B warehouse"
        )
        cls.raw = Ingredient.objects.create(
            business=cls.business, name="Legacy A raw", unit="kg", preparation_level="raw"
        )
        cls.other_raw = Ingredient.objects.create(
            business=cls.other_business, name="Legacy B raw", unit="kg", preparation_level="raw"
        )
        cls.compound = Ingredient.objects.create(
            business=cls.business, name="Legacy A compound", unit="kg",
            preparation_level="semi_prepared",
        )
        cls.other_compound = Ingredient.objects.create(
            business=cls.other_business, name="Legacy B compound", unit="kg",
            preparation_level="semi_prepared",
        )
        cls.recipe = Recipe.objects.create(business=cls.business, name="Legacy A recipe")
        cls.other_recipe = Recipe.objects.create(
            business=cls.other_business, name="Legacy B recipe"
        )

    def test_stock_rejects_foreign_warehouse_update(self):
        stock = Stock.objects.create(warehouse=self.warehouse, ingredient=self.raw)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Stock.objects.filter(pk=stock.pk).update(warehouse_id=self.other_warehouse.pk)

    def test_stock_rejects_foreign_ingredient_update(self):
        stock = Stock.objects.create(warehouse=self.warehouse, ingredient=self.raw)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Stock.objects.filter(pk=stock.pk).update(ingredient_id=self.other_raw.pk)

    def test_compound_component_rejects_foreign_compound_update(self):
        component = CompoundMaterialComponent.objects.create(
            compound=self.compound, ingredient=self.raw,
            quantity=Decimal("1"), unit="kg",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CompoundMaterialComponent.objects.filter(pk=component.pk).update(
                    compound_id=self.other_compound.pk
                )

    def test_compound_component_rejects_foreign_ingredient_update(self):
        component = CompoundMaterialComponent.objects.create(
            compound=self.compound, ingredient=self.raw,
            quantity=Decimal("1"), unit="kg",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CompoundMaterialComponent.objects.filter(pk=component.pk).update(
                    ingredient_id=self.other_raw.pk
                )

    def test_recipe_input_rejects_foreign_recipe_update(self):
        line = RecipeInput.objects.create(
            recipe=self.recipe, ingredient=self.raw,
            quantity=Decimal("1"), unit="kg",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                RecipeInput.objects.filter(pk=line.pk).update(recipe_id=self.other_recipe.pk)

    def test_recipe_input_rejects_foreign_ingredient_update(self):
        line = RecipeInput.objects.create(
            recipe=self.recipe, ingredient=self.raw,
            quantity=Decimal("1"), unit="kg",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                RecipeInput.objects.filter(pk=line.pk).update(ingredient_id=self.other_raw.pk)

    def test_recipe_output_rejects_foreign_recipe_update(self):
        line = RecipeOutput.objects.create(
            recipe=self.recipe, ingredient=self.compound,
            quantity=Decimal("1"), unit="kg", is_primary=True,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                RecipeOutput.objects.filter(pk=line.pk).update(recipe_id=self.other_recipe.pk)

    def test_recipe_output_rejects_foreign_ingredient_update(self):
        line = RecipeOutput.objects.create(
            recipe=self.recipe, ingredient=self.compound,
            quantity=Decimal("1"), unit="kg", is_primary=True,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                RecipeOutput.objects.filter(pk=line.pk).update(ingredient_id=self.other_compound.pk)
