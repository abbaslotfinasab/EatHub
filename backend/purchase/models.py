from django.db import models

from accounts.models import Business, User
from core.models import BaseModel
from inventory.models import Ingredient


class Supplier(BaseModel):

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="suppliers"
    )

    name = models.CharField(
        max_length=150
    )

    phone = models.CharField(
        max_length=30,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    tax_number = models.CharField(
        max_length=100,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    notes = models.TextField(
        blank=True
    )


class PurchaseRequisition(BaseModel):

    class Status(models.TextChoices):

        DRAFT = "draft"
        SUBMITTED = "submitted"
        APPROVED = "approved"
        REJECTED = "rejected"
        COMPLETED = "completed"


    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="purchase_requisitions"
    )

    requested_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT
    )

    reason = models.TextField(
        blank=True
    )


class PurchaseRequisitionItem(BaseModel):

    requisition = models.ForeignKey(
        PurchaseRequisition,
        related_name="items",
        on_delete=models.CASCADE
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3
    )

    note = models.CharField(
        max_length=255,
        blank=True
    )


class PurchaseOrder(BaseModel):

    class Status(models.TextChoices):

        DRAFT = "draft"
        SENT = "sent"
        PARTIAL = "partial"
        RECEIVED = "received"
        CANCELLED = "cancelled"


    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE
    )


    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="purchase_orders"
    )


    requisition = models.ForeignKey(
        PurchaseRequisition,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )


    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT
    )


    order_date = models.DateField()


    expected_date = models.DateField(
        null=True,
        blank=True
    )


    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )


    discount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )


    tax = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )


    total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )


class PurchaseOrderItem(BaseModel):

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        related_name="items",
        on_delete=models.CASCADE
    )


    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT
    )


    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3
    )


    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )


class GoodsReceipt(BaseModel):

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE
    )


    purchase_order = models.ForeignKey(
        PurchaseOrder,
        related_name="receipts",
        on_delete=models.PROTECT
    )


    received_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT
    )


    received_date = models.DateTimeField()


    notes = models.TextField(
        blank=True
    )


class GoodsReceiptItem(BaseModel):

    receipt = models.ForeignKey(
        GoodsReceipt,
        related_name="items",
        on_delete=models.CASCADE
    )


    purchase_order_item = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.PROTECT
    )


    received_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3
    )


    rejected_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0
    )


class PurchaseInvoice(BaseModel):

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        APPROVED = "approved", "Approved"

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="purchase_invoices",
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="purchase_invoices",
    )

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoices",
    )

    invoice_number = models.CharField(
        max_length=100,
    )

    invoice_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    matching_status = models.CharField(
        max_length=20,
        default="not_matched",
        choices=[
            ("not_matched", "Not matched"),
            ("pending_receipt", "Pending receipt"),
            ("matched", "Matched"),
            ("exception", "Exception"),
        ],
    )

    matched_at = models.DateTimeField(null=True, blank=True)

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="approved_purchase_invoices",
    )

    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    discount_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    tax_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    tax_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    total_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business", "invoice_number"],
                name="unique_purchase_invoice_number_per_business",
            ),
        ]


class PurchaseInvoiceItem(BaseModel):

    purchase_invoice = models.ForeignKey(
        "PurchaseInvoice",
        on_delete=models.CASCADE,
        related_name="items",
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name="purchase_invoice_items",
    )

    purchase_order_item = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.PROTECT,
        related_name="purchase_invoice_items",
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
    )

    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    discount_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    tax_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    tax_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    total_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.ingredient} ({self.quantity})"

class SupplierPayment(BaseModel):

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="supplier_payments",
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    invoice = models.ForeignKey(
        PurchaseInvoice,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    payment_date = models.DateField()

    method = models.CharField(
        max_length=50,
    )


class PaymentAllocation(BaseModel):

    payment = models.ForeignKey(
        "SupplierPayment",
        on_delete=models.PROTECT,
        related_name="allocations",
    )

    invoice = models.ForeignKey(
        "PurchaseInvoice",
        on_delete=models.PROTECT,
        related_name="payment_allocations",
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return (
            f"Payment #{self.payment_id} → "
            f"Invoice #{self.invoice_id}: "
            f"{self.amount}"
        )
