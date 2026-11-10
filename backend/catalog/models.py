from django.db import models

from accounts.models import Business
from core.models import BaseModel


class Product(BaseModel):
    """Business-scoped reusable sellable identity; pricing belongs to Sales."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

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
        CELERY = "celery", "Celery"
        CEREALS_GLUTEN = "cereals_gluten", "Cereals containing gluten"
        CRUSTACEANS = "crustaceans", "Crustaceans"
        EGGS = "eggs", "Eggs"
        FISH = "fish", "Fish"
        LUPIN = "lupin", "Lupin"
        MILK = "milk", "Milk"
        MOLLUSCS = "molluscs", "Molluscs"
        MUSTARD = "mustard", "Mustard"
        PEANUTS = "peanuts", "Peanuts"
        SESAME = "sesame", "Sesame"
        SOYBEANS = "soybeans", "Soybeans"
        SULPHITES = "sulphites", "Sulphur dioxide and sulphites"
        TREE_NUTS = "tree_nuts", "Tree nuts"

    class Presence(models.TextChoices):
        CONTAINS = "contains", "Contains"
        MAY_CONTAIN = "may_contain", "May contain"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="allergen_declarations")
    code = models.CharField(max_length=32, choices=Code.choices)
    presence = models.CharField(max_length=16, choices=Presence.choices, default=Presence.CONTAINS)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("product", "code"), name="catalog_product_allergen_uq"),
            # Nested Meta classes cannot resolve sibling nested TextChoices classes.
            # Keep the DB enum allow-lists explicit here, matching the model choices.
            models.CheckConstraint(condition=models.Q(code__in=("celery", "cereals_gluten", "crustaceans", "eggs", "fish", "lupin", "milk", "molluscs", "mustard", "peanuts", "sesame", "soybeans", "sulphites", "tree_nuts")), name="cat_prod_allergen_code_ck"),
            models.CheckConstraint(condition=models.Q(presence__in=("contains", "may_contain")), name="cat_prod_allergen_presence_ck"),
        ]
        ordering = ("code",)


class ProductDietaryTag(BaseModel):
    """Business-entered dietary suitability tags; not certification claims."""

    class Code(models.TextChoices):
        VEGAN = "vegan", "Vegan"
        VEGETARIAN = "vegetarian", "Vegetarian"
        GLUTEN_FREE = "gluten_free", "Gluten-free"
        DAIRY_FREE = "dairy_free", "Dairy-free"
        HALAL = "halal", "Halal"
        KOSHER = "kosher", "Kosher"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="dietary_tags")
    code = models.CharField(max_length=24, choices=Code.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("product", "code"), name="catalog_product_dietary_tag_uq"),
            models.CheckConstraint(condition=models.Q(code__in=("vegan", "vegetarian", "gluten_free", "dairy_free", "halal", "kosher")), name="cat_prod_dietary_code_ck"),
        ]
        ordering = ("code",)
