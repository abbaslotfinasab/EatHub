from django.db import models

from accounts.models import Business, User
from core.models import BaseModel


class Customer(BaseModel):
    """A business-scoped customer identity owned by the Customer module.

    The explicit table name preserves the existing products_customer table while
    model ownership moves between Django apps.
    """

    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        db_table = "products_customer"
