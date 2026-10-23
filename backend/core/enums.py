from django.db import models


class PermissionCode(models.TextChoices):

    # Orders
    ORDERS_VIEW = "orders.view", "View Orders"
    ORDERS_CREATE = "orders.create", "Create Orders"
    ORDERS_UPDATE = "orders.update", "Update Orders"
    ORDERS_CANCEL = "orders.cancel", "Cancel Orders"
    PAYMENTS_MANAGE = "payments.manage", "Manage Payments and Refunds"

    # Products
    PRODUCTS_VIEW = "products.view", "View Products"
    PRODUCTS_CREATE = "products.create", "Create Products"
    PRODUCTS_UPDATE = "products.update", "Update Products"
    PRODUCTS_DELETE = "products.delete", "Delete Products"

    # Inventory
    INVENTORY_VIEW = "inventory.view", "View Inventory"
    INVENTORY_ADJUST = "inventory.adjust", "Adjust Inventory"

    # Purchase
    PURCHASE_VIEW = "purchase.view", "View Purchase Data"
    PURCHASE_REQUISITION_VIEW_OWN = "purchase.requisition.view_own", "View Own Purchase Requisitions"
    PURCHASE_REQUISITION_CREATE = "purchase.requisition.create", "Create Purchase Requisitions"
    PURCHASE_REQUISITION_SUBMIT = "purchase.requisition.submit", "Submit Purchase Requisitions"
    PURCHASE_REQUISITION_APPROVE = "purchase.requisition.approve", "Approve or Reject Purchase Requisitions"
    PURCHASE_SUPPLIER_MANAGE = "purchase.supplier.manage", "Manage Suppliers"
    PURCHASE_ORDER_CREATE = "purchase.order.create", "Create Purchase Orders"
    PURCHASE_ORDER_UPDATE = "purchase.order.update", "Update Draft Purchase Orders"
    PURCHASE_ORDER_DISPATCH = "purchase.order.dispatch", "Dispatch Purchase Orders"
    PURCHASE_ORDER_CANCEL = "purchase.order.cancel", "Cancel Purchase Orders"
    PURCHASE_RECEIPT_CREATE = "purchase.receipt.create", "Create Goods Receipts"
    PURCHASE_INVOICE_CREATE = "purchase.invoice.create", "Create Purchase Invoices"
    PURCHASE_INVOICE_UPDATE = "purchase.invoice.update", "Update Draft Purchase Invoices"
    PURCHASE_INVOICE_MATCH = "purchase.invoice.match", "Match Purchase Invoices"
    PURCHASE_INVOICE_APPROVE = "purchase.invoice.approve", "Approve Purchase Invoices"
    PURCHASE_INVOICE_POST = "purchase.invoice.post", "Post Purchase Invoices"
    PURCHASE_INVOICE_CANCEL = "purchase.invoice.cancel", "Cancel Purchase Invoices"
    PURCHASE_PAYMENT_CREATE = "purchase.payment.create", "Create Supplier Payments"
    PURCHASE_PAYMENT_ALLOCATE = "purchase.payment.allocate", "Allocate Supplier Payments"

    # Reports
    REPORTS_VIEW_SALES = "reports.view_sales", "View Sales Report"

    # Employees
    EMPLOYEES_VIEW = "employees.view", "View Employees"
    EMPLOYEES_CREATE = "employees.create", "Create Employees"



