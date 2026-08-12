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
        ]

    def __str__(self):
        return self.name



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
        PURCHASE = "purchase", "Purchase"
        PRODUCTION_IN = "production_in", "Production In"
        PRODUCTION_OUT = "production_out", "Production Out"
        SALE = "sale", "Sale"
        WASTE = "waste", "Waste"
        ADJUSTMENT = "adjustment", "Adjustment"
        TRANSFER_IN = "transfer_in", "Transfer In"
        TRANSFER_OUT = "transfer_out", "Transfer Out"

    stock = models.ForeignKey(
        Stock,
        on_delete=models.PROTECT,
        related_name="transactions",
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
    )

    type = models.CharField(
        max_length=30,
        choices=Type.choices,
    )

    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    reference_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )

    reference_id = models.PositiveIntegerField(
        blank=True,
        null=True,
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-created_at"]


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
        max_digits=12,
        decimal_places=3,
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
                name="unique_recipe_input_ingredient",
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
        max_digits=12,
        decimal_places=3,
    )

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
            models.UniqueConstraint(
                fields=["recipe"],
                condition=models.Q(is_primary=True),
                name="unique_primary_output_per_recipe",
            ),
        ]

class PurchaseOrder(BaseModel):

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ORDERED = "ordered", "Ordered"
        PARTIALLY_RECEIVED = "partially_received", "Partially Received"
        RECEIVED = "received", "Received"
        CANCELLED = "cancelled", "Cancelled"

    class Type(models.TextChoices):
        PURCHASE = "purchase", "Purchase"
        SALES = "sales", "Sales"

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="purchase_orders",
    )

    supplier_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
    )

    supplier_name = models.CharField(
        max_length=150,
    )

    supplier_number = models.CharField(
        max_length=30,
        blank=True,
        default="",
    )

    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.PURCHASE,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    invoice_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    notes = models.TextField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"PO-{self.id}"


class PurchaseOrderItem(BaseModel):

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="items",
    )

    item_type = models.CharField(
        choices=[
            ("ingredient", "Ingredient"),
            ("menu_item", "Menu Item"),
        ]
    )

    item_id = models.PositiveIntegerField()

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.ingredient} ({self.quantity})"