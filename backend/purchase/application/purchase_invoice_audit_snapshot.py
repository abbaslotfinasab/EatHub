from datetime import date, datetime
from decimal import Decimal
from enum import Enum


def json_safe(value):
    """Normalize values used in audit metadata to JSON-compatible primitives."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if hasattr(value, "items") and not isinstance(value, (str, bytes)):
        return {str(key): json_safe(item) for key, item in value.items()}
    return value


def build_purchase_invoice_snapshot(invoice):
    """Build the stable before/after audit snapshot for a purchase invoice."""
    return json_safe({
        "invoice_number": invoice.invoice_number,
        "invoice_date": invoice.invoice_date,
        "supplier_id": invoice.supplier_id,
        "purchase_order_id": invoice.purchase_order_id,
        "status": invoice.status,
        "subtotal": invoice.subtotal,
        "total_price": invoice.total_price,
        "items": [
            {
                "id": item.id,
                "ingredient_id": item.ingredient_id,
                "purchase_order_item_id": item.purchase_order_item_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "discount_percent": item.discount_percent,
                "tax_percent": item.tax_percent,
                "total_price": item.total_price,
            }
            for item in invoice.items
        ],
    })
