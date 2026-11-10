from django.conf import settings
from django.db import models

from core.models import BaseModel


class CustomerAccount(BaseModel):
    business = models.ForeignKey("accounts.Business", on_delete=models.CASCADE)
    customer = models.OneToOneField(
        "customer.Customer",
        on_delete=models.CASCADE,
        related_name="account",
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ledger_opening_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    ledger_opening_balance_verified = models.BooleanField(default=False)

    class Meta:
        db_table = "products_customeraccount"


class OrderRefund(BaseModel):
    """Auditable record of a completed full refund for an order."""

    order = models.ForeignKey(
        "products.Order", on_delete=models.PROTECT, related_name="refunds"
    )
    business = models.ForeignKey(
        "accounts.Business", on_delete=models.PROTECT, related_name="order_refunds"
    )
    customer = models.ForeignKey(
        "customer.Customer",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="order_refunds",
    )
    payment_method = models.CharField(
        max_length=30,
        choices=[
            ("cash", "Cash"),
            ("card", "Card"),
            ("customer_account", "Customer Account"),
        ],
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    reference = models.CharField(max_length=200, blank=True)
    idempotency_key = models.UUIDField(unique=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="order_refunds",
    )

    class Meta:
        db_table = "products_orderrefund"
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
        related_name="transactions",
    )
    order = models.ForeignKey(
        "products.Order", null=True, blank=True, on_delete=models.SET_NULL
    )
    type = models.CharField(max_length=10, choices=Type.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
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
        db_table = "products_customertransaction"
        constraints = [
            models.UniqueConstraint(
                fields=("refund",),
                condition=models.Q(refund__isnull=False),
                name="uniq_txn_refund",
            ),
        ]
