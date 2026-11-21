from django.db import models

from accounts.models import Business
from catalog.choices import (
    ALLERGEN_CELERY,
    ALLERGEN_CEREALS_GLUTEN,
    ALLERGEN_CRUSTACEANS,
    ALLERGEN_EGGS,
    ALLERGEN_FISH,
    ALLERGEN_LUPIN,
    ALLERGEN_MILK,
    ALLERGEN_MOLLUSCS,
    ALLERGEN_MUSTARD,
    ALLERGEN_PEANUTS,
    ALLERGEN_PRESENCE_CONTAINS,
    ALLERGEN_PRESENCE_MAY_CONTAIN,
    ALLERGEN_SESAME,
    ALLERGEN_SOYBEANS,
    ALLERGEN_SULPHITES,
    ALLERGEN_TREE_NUTS,
    DIETARY_TAG_DAIRY_FREE,
    DIETARY_TAG_GLUTEN_FREE,
    DIETARY_TAG_HALAL,
    DIETARY_TAG_KOSHER,
    DIETARY_TAG_VEGAN,
    DIETARY_TAG_VEGETARIAN,
    PRODUCT_STATUS_ACTIVE,
    PRODUCT_STATUS_ARCHIVED,
    PRODUCT_STATUS_DRAFT,
)
from core.models import BaseModel


class Product(BaseModel):
    """Business-scoped reusable sellable identity; pricing belongs to Sales."""

    class Status(models.TextChoices):
        DRAFT = PRODUCT_STATUS_DRAFT, "Draft"
        ACTIVE = PRODUCT_STATUS_ACTIVE, "Active"
        ARCHIVED = PRODUCT_STATUS_ARCHIVED, "Archived"

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="catalog_products")
    name = models.CharField(max_length=120)
    sku = models.CharField(max_length=50, blank=True, null=True)
    category = models.CharField(max_length=120, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image_url = models.CharField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(fields=("business", "sku"), condition=models.Q(sku__isnull=False) & ~models.Q(sku=""), name="catalog_product_business_sku_uq"),
            models.CheckConstraint(condition=models.Q(status__in=("draft", "active", "archived")), name="catalog_product_status_ck"),
        ]
        indexes = [models.Index(fields=("business", "status", "name"), name="catalog_prod_scope_status_ix")]

    def __str__(self):
        return self.name


class ProductAllergen(BaseModel):
    """Declared allergen presence; not a substitute for legal label review."""

    class Code(models.TextChoices):
        CELERY = ALLERGEN_CELERY, "Celery"
        CEREALS_GLUTEN = ALLERGEN_CEREALS_GLUTEN, "Cereals containing gluten"
        CRUSTACEANS = ALLERGEN_CRUSTACEANS, "Crustaceans"
        EGGS = ALLERGEN_EGGS, "Eggs"
        FISH = ALLERGEN_FISH, "Fish"
        LUPIN = ALLERGEN_LUPIN, "Lupin"
        MILK = ALLERGEN_MILK, "Milk"
        MOLLUSCS = ALLERGEN_MOLLUSCS, "Molluscs"
        MUSTARD = ALLERGEN_MUSTARD, "Mustard"
        PEANUTS = ALLERGEN_PEANUTS, "Peanuts"
        SESAME = ALLERGEN_SESAME, "Sesame"
        SOYBEANS = ALLERGEN_SOYBEANS, "Soybeans"
        SULPHITES = ALLERGEN_SULPHITES, "Sulphur dioxide and sulphites"
        TREE_NUTS = ALLERGEN_TREE_NUTS, "Tree nuts"

    class Presence(models.TextChoices):
        CONTAINS = ALLERGEN_PRESENCE_CONTAINS, "Contains"
        MAY_CONTAIN = ALLERGEN_PRESENCE_MAY_CONTAIN, "May contain"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="allergen_declarations")
    code = models.CharField(max_length=32, choices=Code.choices)
    presence = models.CharField(max_length=16, choices=Presence.choices, default=Presence.CONTAINS)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("product", "code"), name="catalog_product_allergen_uq"),
            models.CheckConstraint(condition=models.Q(code__in=("celery", "cereals_gluten", "crustaceans", "eggs", "fish", "lupin", "milk", "molluscs", "mustard", "peanuts", "sesame", "soybeans", "sulphites", "tree_nuts")), name="cat_prod_allergen_code_ck"),
            models.CheckConstraint(condition=models.Q(presence__in=("contains", "may_contain")), name="cat_prod_allergen_presence_ck"),
        ]
        ordering = ("code",)


class ProductDietaryTag(BaseModel):
    """Business-entered dietary suitability tags; not certification claims."""

    class Code(models.TextChoices):
        VEGAN = DIETARY_TAG_VEGAN, "Vegan"
        VEGETARIAN = DIETARY_TAG_VEGETARIAN, "Vegetarian"
        GLUTEN_FREE = DIETARY_TAG_GLUTEN_FREE, "Gluten-free"
        DAIRY_FREE = DIETARY_TAG_DAIRY_FREE, "Dairy-free"
        HALAL = DIETARY_TAG_HALAL, "Halal"
        KOSHER = DIETARY_TAG_KOSHER, "Kosher"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="dietary_tags")
    code = models.CharField(max_length=24, choices=Code.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("product", "code"), name="catalog_product_dietary_tag_uq"),
            models.CheckConstraint(condition=models.Q(code__in=("vegan", "vegetarian", "gluten_free", "dairy_free", "halal", "kosher")), name="cat_prod_dietary_code_ck"),
        ]
        ordering = ("code",)
