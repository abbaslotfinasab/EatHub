from decimal import Decimal
from unittest import skipUnless

from django.db import IntegrityError, connection, transaction
from django.test import TestCase

from accounts.models import Business
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
