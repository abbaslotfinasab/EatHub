from django.db import models

from core.models import BaseModel

from accounts.models import Business



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

    image_url = models.URLField(
        null=True,
        blank=True
    )
    is_available = models.BooleanField(default=True)


class Order(BaseModel):

    class Status(models.TextChoices):
        PENDING = "pending"
        CONFIRMED = "confirmed"
        PREPARING = "preparing"
        READY = "ready"
        COMPLETED = "completed"
        CANCELLED = "cancelled"
        FAILED = "failed"

    class OrderType(models.TextChoices):
        DINE_IN = "dine_in"
        TAKEAWAY = "takeaway"
        DELIVERY = "delivery"

    business = models.ForeignKey(Business, on_delete=models.CASCADE)

    customer_name = models.CharField(max_length=120)
    customer_phone = models.CharField(max_length=20, null=True, blank=True)

    order_type = models.CharField(max_length=20, choices=OrderType.choices)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    payment_status = models.CharField(max_length=20, default="pending")

    notes = models.TextField(null=True, blank=True)

class OrderItem(BaseModel):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)

    menuItem = models.ForeignKey(MenuItem, on_delete=models.PROTECT)

    quantity = models.PositiveIntegerField()

    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    total_price = models.DecimalField(max_digits=12, decimal_places=2)