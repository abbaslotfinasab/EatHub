from django.db import models

from accounts.models import Business
from core.models import BaseModel


class Product(BaseModel):
    """Business-scoped reusable sellable identity; pricing belongs to Sales."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="catalog_products",
    )
    name = models.CharField(max_length=120)
    sku = models.CharField(max_length=50, blank=True, null=True)
    category = models.CharField(max_length=120, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image_url = models.CharField(max_length=500, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=("business", "sku"),
                condition=models.Q(sku__isnull=False) & ~models.Q(sku=""),
                name="catalog_product_business_sku_uq",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=("draft", "active", "archived")),
                name="catalog_product_status_ck",
            ),
        ]
        indexes = [
            models.Index(fields=("business", "status", "name"), name="catalog_prod_scope_status_ix"),
        ]

    def __str__(self):
        return self.name
