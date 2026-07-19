from django.db import models

from core.models import BaseModel

from accounts.models import Business, User


class Menu(BaseModel):

    business = models.ForeignKey(Business, on_delete=models.CASCADE)

    name = models.CharField(max_length=120)
    category = models.CharField(max_length=120)

    description = models.TextField(null=True, blank=True)

    sort_order = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True)

class MenuItem(BaseModel):

    business = models.ForeignKey(Business, on_delete=models.CASCADE)

    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name="items")

    name = models.CharField(max_length=120)
    description = models.TextField(null=True, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)

    image_url = models.CharField(
        max_length=500,
        null=True,
        blank=True
    )

    is_available = models.BooleanField(default=True)


class Customer(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE)

    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)

    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(auto_now_add=True)


class Order(BaseModel):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PREPARING = "preparing", "Preparing"
        READY = "ready", "Ready"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        FAILED = "failed", "Failed"

    class OrderType(models.TextChoices):
        DINE_IN = "dine_in", "Dine In"
        TAKEAWAY = "takeaway", "Takeaway"
        DELIVERY = "delivery", "Delivery"

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        UNPAID = "unpaid"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    business = models.ForeignKey(Business, on_delete=models.CASCADE)

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)

    table = models.IntegerField(null=True, blank=True)

    order_type = models.CharField(
        max_length=20,
        choices=OrderType.choices,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )

    notes = models.TextField(null=True, blank=True)

class OrderItem(BaseModel):
    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE,
    )

    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT,
    )

    menu_item_name = models.CharField(max_length=120)

    quantity = models.PositiveIntegerField()

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    notes = models.TextField(
        null=True,
        blank=True,
    )




class CustomerAccount(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name="account")

    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CustomerTransaction(models.Model):

    class Type(models.TextChoices):
        CREDIT = "credit", "Credit"
        DEBIT = "debit", "Debit"
        ADJUST = "adjust", "Adjust"

    account = models.ForeignKey(
        CustomerAccount,
        on_delete=models.CASCADE,
        related_name="transactions"
    )

    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.SET_NULL)

    type = models.CharField(max_length=10, choices=Type.choices)

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    description = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)