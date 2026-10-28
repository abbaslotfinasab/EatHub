from decimal import Decimal

from django.db import models

from accounts.models import Business
from core.models import BaseModel


class Warehouse(BaseModel):

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="warehouses",
    )

    name = models.CharField(
        max_length=120,
    )

    code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    is_default = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["business", "name"],
                name="unique_warehouse_name_per_business",
            ),
            models.UniqueConstraint(
                fields=["business"],
                condition=models.Q(is_active=True, is_default=True),
                name="inv_wh_active_default_uq",
            ),
        ]

    def __str__(self):
        return self.name



class Ingredient(BaseModel):

    class Unit(models.TextChoices):
        KG = "kg", "Kilogram"
        G = "g", "Gram"
        L = "l", "Liter"
        ML = "ml", "Milliliter"
        PIECE = "pc", "Piece"
        PACK = "pk", "Pack"

    class PreparationLevel(models.TextChoices):
        RAW = "raw", "Raw"
        SEMI_PREPARED = "semi_prepared", "Semi Prepared"

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="ingredients",
    )

    name = models.CharField(
        max_length=120,
    )

    sku = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )

    unit = models.CharField(
        max_length=10,
        choices=Unit.choices,
    )

    preparation_level = models.CharField(
        max_length=20,
        choices=PreparationLevel.choices,
        default=PreparationLevel.RAW,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["business", "name"],
                name="unique_ingredient_name_per_business",
            ),
            models.UniqueConstraint(
                fields=["business", "sku"],
                condition=models.Q(sku__isnull=False) & ~models.Q(sku=""),
                name="inv_item_business_sku_uq",
            ),
        ]

    def __str__(self):
        return self.name


UNIT_VALUES = tuple(value for value, _label in Ingredient.Unit.choices)


class CompoundMaterialComponent(BaseModel):
    """A non-stock recipe line defining the raw inputs of a compound material."""

    compound = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name="compound_components",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name="used_in_compound_materials",
    )
    quantity = models.DecimalField(max_digits=36, decimal_places=12)
    unit = models.CharField(max_length=2, choices=Ingredient.Unit.choices)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["compound", "ingredient"],
                name="inv_compound_component_uq",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(quantity__gt=0)
                    & models.Q(quantity__lte=Decimal("999999999999999999999999.999999999999"))
                ),
                name="inv_compound_component_qty_ck",
            ),
            models.CheckConstraint(
                condition=~models.Q(compound=models.F("ingredient")),
                name="inv_compound_not_self_ck",
            ),
        ]



class Stock(BaseModel):

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="stocks",
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name="stocks",
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
    )

    average_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    reorder_level = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
    )

    reorder_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["warehouse", "ingredient"],
                name="unique_stock_per_warehouse_ingredient",
            ),
        ]

class StockTransaction(BaseModel):

    class Type(models.TextChoices):

        OPENING = "opening"

        PURCHASE_RECEIVE = "purchase_receive"

        PURCHASE = "purchase"

        PRODUCTION_IN = "production_in"

        PRODUCTION_OUT = "production_out"

        SALE = "sale"

        WASTE = "waste"

        ADJUSTMENT = "adjustment"

        TRANSFER_IN = "transfer_in"

        TRANSFER_OUT = "transfer_out"


    stock = models.ForeignKey(
        Stock,
        on_delete=models.PROTECT,
        related_name="transactions"
    )


    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3
    )


    unit_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )


    type = models.CharField(
        max_length=40,
        choices=Type.choices
    )


    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True
    )


    reference_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )


    reference_id = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    description = models.TextField(
        blank=True,
        null=True,
    )



class Recipe(BaseModel):

    class Type(models.TextChoices):
        PRODUCTION = "production", "Production"
        PREPARATION = "preparation", "Preparation"

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="recipes",
    )

    name = models.CharField(
        max_length=150,
    )

    code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )

    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.PREPARATION,
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["name"]

        constraints = [
            models.UniqueConstraint(
                fields=["business", "name"],
                name="unique_recipe_name_per_business",
            ),
        ]

    def __str__(self):
        return self.name



class RecipeInput(BaseModel):

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="inputs",
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name="recipe_inputs",
    )

    quantity = models.DecimalField(
        max_digits=36,
        decimal_places=12,
    )

    unit = models.CharField(max_length=2, choices=Ingredient.Unit.choices)

    notes = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_input_ingredient",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(quantity__gt=0)
                    & models.Q(quantity__lte=Decimal("999999999999999999999999.999999999999"))
                ),
                name="recipe_input_quantity_positive_ck",
            ),
            models.CheckConstraint(
                condition=models.Q(unit__in=UNIT_VALUES),
                name="recipe_input_unit_supported_ck",
            ),
        ]

class RecipeOutput(BaseModel):

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="outputs",
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name="recipe_outputs",
    )

    quantity = models.DecimalField(
        max_digits=36,
        decimal_places=12,
    )

    unit = models.CharField(max_length=2, choices=Ingredient.Unit.choices)

    is_primary = models.BooleanField(
        default=False,
    )

    notes = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_output_ingredient",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(quantity__gt=0)
                    & models.Q(quantity__lte=Decimal("999999999999999999999999.999999999999"))
                ),
                name="recipe_output_quantity_positive_ck",
            ),
            models.CheckConstraint(
                condition=models.Q(unit__in=UNIT_VALUES),
                name="recipe_output_unit_supported_ck",
            ),
            models.UniqueConstraint(
                fields=["recipe"],
                condition=models.Q(is_primary=True),
                name="unique_primary_output_per_recipe",
            ),
        ]


# Register additive V1 persistence models with Django's standard app model loader.
# The legacy models above remain unchanged and retain their existing tables.
from inventory.infrastructure.django.models import (  # noqa: E402
    InventoryV1Stock,
    InventoryV1StockMovement,
    InventoryOperation,
    InventoryOperationLine,
    InventoryReservation,
    InventoryReservationLine,
)
