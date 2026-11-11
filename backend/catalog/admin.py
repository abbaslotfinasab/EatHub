from django.contrib import admin

from catalog.models import Product, ProductAllergen, ProductDietaryTag


class ProductAllergenInline(admin.TabularInline):
    model = ProductAllergen
    extra = 0


class ProductDietaryTagInline(admin.TabularInline):
    model = ProductDietaryTag
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "sku", "category", "status", "business")
    list_filter = ("status", "business")
    search_fields = ("name", "sku", "category")
    inlines = (ProductAllergenInline, ProductDietaryTagInline)
