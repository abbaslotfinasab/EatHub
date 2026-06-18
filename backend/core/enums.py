from django.db import models


class PermissionCode(models.TextChoices):

    # Orders
    ORDERS_VIEW = "orders.view", "View Orders"
    ORDERS_CREATE = "orders.create", "Create Orders"
    ORDERS_UPDATE = "orders.update", "Update Orders"
    ORDERS_CANCEL = "orders.cancel", "Cancel Orders"

    # Products
    PRODUCTS_VIEW = "products.view", "View Products"
    PRODUCTS_CREATE = "products.create", "Create Products"
    PRODUCTS_UPDATE = "products.update", "Update Products"
    PRODUCTS_DELETE = "products.delete", "Delete Products"

    # Inventory
    INVENTORY_VIEW = "inventory.view", "View Inventory"
    INVENTORY_ADJUST = "inventory.adjust", "Adjust Inventory"

    # Reports
    REPORTS_VIEW_SALES = "reports.view_sales", "View Sales Report"

    # Employees
    EMPLOYEES_VIEW = "employees.view", "View Employees"
    EMPLOYEES_CREATE = "employees.create", "Create Employees"



