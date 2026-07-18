from django.db import models

from accounts.models import Business
from core.models import BaseModel
from products.models import MenuItem



class Ingredient(BaseModel):

    class Unit(models.TextChoices):
        KG = "kg", "Kilogram"
        G = "g", "Gram"
        L = "l", "Liter"
        ML = "ml", "Milliliter"
        PIECE = "pc", "Piece"
        PACK = "pk", "Pack"

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

    current_stock = models.DecimalField(
        max_digits=12,
        decimal_places=3,
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

    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    complete = models.BooleanField(
        default=False,
        help_text="Prepared ingredient (e.g. dough, sauce, cooked chicken)",
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["name"]
        unique_together = (
            "business",
            "name",
        )

    def __str__(self):
        return self.name



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