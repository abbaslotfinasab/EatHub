from decimal import Decimal

from django.core.exceptions import ValidationError
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

    recipe = models.OneToOneField(
        "inventory.Recipe",
        on_delete=models.PROTECT,
        related_name="menu_item",
        null=True,
        blank=True,
    )

    is_available = models.BooleanField(default=True)


class Customer(BaseModel):
    business = models.ForeignKey(Business, on_delete=models.CASCADE)

    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)

    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )


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

    class PaymentMethod(models.TextChoices):
        CASH = "cash"
        CARD = "card"
        CUSTOMER_ACCOUNT = "customer_account"

    business = models.ForeignKey(Business, on_delete=models.CASCADE)

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="orders",
    )
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

    payment_method = models.CharField(
        max_length=30,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
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
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
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




class CustomerAccount(BaseModel):
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name="account")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ledger_opening_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0")
    )
    ledger_opening_balance_verified = models.BooleanField(default=False)



class OrderRefund(BaseModel):
    """Auditable record of a completed full refund for an order."""

    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="refunds")
    business = models.ForeignKey(
        Business, on_delete=models.PROTECT, related_name="order_refunds"
    )
    customer = models.ForeignKey(
        Customer,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="order_refunds",
    )
    payment_method = models.CharField(max_length=30, choices=Order.PaymentMethod.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    reference = models.CharField(max_length=200, blank=True)
    idempotency_key = models.UUIDField(unique=True)
    actor = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="order_refunds",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="order_refund_positive_amt",
            ),
        ]


class CustomerTransaction(BaseModel):

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

    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    # Marks ledger entries that form the immutable settlement history for an order.
    # Ordinary customer credits/debits may also carry an order reference and must
    # not be mistaken for payment reconciliation. Historical rows may have been
    # classified by migration heuristics, so reconciliation also requires the
    # explicit verification marker below.
    is_order_settlement = models.BooleanField(default=False)

    is_order_settlement_verified = models.BooleanField(default=False)

    refund = models.ForeignKey(
        OrderRefund,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="transactions",
    )

    description = models.TextField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("refund",),
                condition=models.Q(refund__isnull=False),
                name="uniq_txn_refund",
            ),
        ]


INVENTORY_UNITS = (("kg", "kg"), ("g", "g"), ("l", "l"), ("ml", "ml"), ("pc", "pc"), ("pk", "pk"))


class OrderItemRecipeSnapshot(models.Model):
    """Immutable recipe/yield basis captured when an order is confirmed."""

    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="order_recipe_snapshots")
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="recipe_snapshots")
    order_item = models.OneToOneField(
        OrderItem, on_delete=models.PROTECT, related_name="inventory_recipe_snapshot"
    )
    recipe = models.ForeignKey("inventory.Recipe", on_delete=models.PROTECT, related_name="order_snapshots")
    recipe_output_ingredient = models.ForeignKey(
        "inventory.Ingredient", on_delete=models.PROTECT, related_name="order_output_snapshots"
    )
    recipe_updated_at = models.DateTimeField()
    output_quantity = models.DecimalField(max_digits=36, decimal_places=12)
    output_unit = models.CharField(max_length=2, choices=INVENTORY_UNITS)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_item_recipe_snapshot"
        indexes = [models.Index(fields=("business", "order"), name="order_snapshot_scope_ix")]
        constraints = [
            models.CheckConstraint(condition=models.Q(output_quantity__gt=0), name="order_recipe_snapshot_yield_ck"),
            models.CheckConstraint(condition=models.Q(output_unit="pc"), name="order_recipe_snapshot_unit_ck"),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Confirmed order recipe snapshots are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Confirmed order recipe snapshots are retained for audit.")


class OrderItemIngredientRequirement(models.Model):
    """Immutable canonical-unit requirement derived from a recipe snapshot."""

    snapshot = models.ForeignKey(
        OrderItemRecipeSnapshot, on_delete=models.PROTECT, related_name="requirements"
    )
    ingredient = models.ForeignKey(
        "inventory.Ingredient", on_delete=models.PROTECT, related_name="order_requirements"
    )
    recipe_input_id = models.PositiveBigIntegerField()
    standard_quantity = models.DecimalField(max_digits=36, decimal_places=12)
    unit = models.CharField(max_length=2, choices=INVENTORY_UNITS)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_item_ingredient_requirement"
        constraints = [
            models.UniqueConstraint(fields=("snapshot", "ingredient"), name="order_req_snapshot_item_uq"),
            models.CheckConstraint(condition=models.Q(standard_quantity__gt=0), name="order_req_qty_positive_ck"),
            models.CheckConstraint(condition=models.Q(unit__in=("kg", "g", "l", "ml", "pc", "pk")), name="order_req_unit_ck"),
            models.CheckConstraint(condition=models.Q(recipe_input_id__gt=0), name="order_req_input_id_ck"),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Confirmed order ingredient requirements are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Confirmed order ingredient requirements are retained for audit.")


class OrderInventoryConsumption(BaseModel):
    """Idempotent actual-consumption posting for one order."""

    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="inventory_consumptions")
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="inventory_consumptions")
    idempotency_key = models.UUIDField()
    payload_fingerprint = models.CharField(max_length=64)
    actor = models.ForeignKey(User, on_delete=models.PROTECT, related_name="inventory_consumptions")
    inventory_operation = models.ForeignKey(
        "inventory.InventoryOperation", null=True, blank=True, on_delete=models.PROTECT,
        related_name="order_consumptions",
    )

    class Meta:
        db_table = "order_inventory_consumption"
        constraints = [
            models.UniqueConstraint(fields=("business", "idempotency_key"), name="order_consumption_idem_uq"),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            previous = type(self).objects.get(pk=self.pk)
            immutable = (
                "business_id", "order_id", "idempotency_key", "payload_fingerprint", "actor_id"
            )
            if any(getattr(previous, field) != getattr(self, field) for field in immutable):
                raise ValidationError("Posted order consumption headers are immutable.")
            if previous.inventory_operation_id and previous.inventory_operation_id != self.inventory_operation_id:
                raise ValidationError("A consumption operation link cannot be changed.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Posted order consumption history is retained for audit.")


class OrderInventoryConsumptionLine(models.Model):
    consumption = models.ForeignKey(
        OrderInventoryConsumption, on_delete=models.PROTECT, related_name="lines"
    )
    requirement = models.ForeignKey(
        OrderItemIngredientRequirement, on_delete=models.PROTECT, related_name="consumption_lines"
    )
    actual_quantity = models.DecimalField(max_digits=36, decimal_places=12)
    unit = models.CharField(max_length=2, choices=INVENTORY_UNITS)
    inventory_movement = models.ForeignKey(
        "inventory.InventoryV1StockMovement", null=True, blank=True, on_delete=models.PROTECT,
        related_name="order_consumption_lines",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_inventory_consumption_line"
        constraints = [
            models.UniqueConstraint(fields=("consumption", "requirement"), name="order_consumption_req_uq"),
            models.CheckConstraint(condition=models.Q(actual_quantity__gte=0), name="order_consumption_qty_nonneg_ck"),
            models.CheckConstraint(condition=models.Q(unit__in=("kg", "g", "l", "ml", "pc", "pk")), name="order_consumption_unit_ck"),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            previous = type(self).objects.get(pk=self.pk)
            immutable = ("consumption_id", "requirement_id", "actual_quantity", "unit")
            if any(getattr(previous, field) != getattr(self, field) for field in immutable):
                raise ValidationError("Posted order consumption lines are immutable.")
            if previous.inventory_movement_id and previous.inventory_movement_id != self.inventory_movement_id:
                raise ValidationError("A consumption line's movement link cannot be changed.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Posted order consumption history is retained for audit.")

