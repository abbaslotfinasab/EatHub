from django.contrib import admin

from catalog.models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "sku", "category", "status", "business")
    list_filter = ("status", "business")
    search_fields = ("name", "sku", "category")
