from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ActivityLog(BaseModel):
    class Action(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"

        ORDER_CREATED = "order_created", "Order Created"
        ORDER_COMPLETED = "order_completed", "Order Completed"
        ORDER_CANCELLED = "order_cancelled", "Order Cancelled"

        STOCK_LOW = "stock_low", "Stock Low"

        LOGIN = "login", "Login"

    business = models.ForeignKey(
        "accounts.Business",
        on_delete=models.CASCADE,
        related_name="activities",
    )

    user = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    action = models.CharField(
        max_length=50,
        choices=Action.choices,
    )

    title = models.CharField(
        max_length=200,
    )

    description = models.TextField(
        null=True,
        blank=True,
    )

    entity_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )

    entity_id = models.IntegerField(
        null=True,
        blank=True,
    )
