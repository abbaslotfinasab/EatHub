from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404

from inventory.models import (
    PurchaseOrder,
    PurchaseOrderItem,
    Ingredient,
)
from products.models import MenuItem


class PurchaseOrderService:

    @staticmethod
    @transaction.atomic
    def create_from_order(*, order):

        invoice = PurchaseOrder.objects.create(
            business=order.business,
            supplier_name=order.customer.name or "Customer",
            supplier_number=order.customer.phone or "",
            type=PurchaseOrder.Type.SALES,
            status=PurchaseOrder.Status.ORDERED,
            subtotal=order.subtotal,
            discount=order.discount,
            tax=order.tax,
            total_amount=order.total_amount,
            notes=f"Invoice for Order #{order.id}",
        )

        for item in order.items.all():
            PurchaseOrderItem.objects.create(
                purchase_order=invoice,
                item_type="menu_item",
                item_id=item.menu_item_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
            )

        return invoice

    @staticmethod
    @transaction.atomic
    def create_purchase_order(*, business, validated_data):

        items_data = validated_data.pop("items")

        # 1. Create Purchase Order (header)
        po = PurchaseOrder.objects.create(
            business=business,
            supplier_id=validated_data.get("supplier_id"),
            supplier_name=validated_data["supplier_name"],
            supplier_number=validated_data.get("supplier_number", ""),
            type=PurchaseOrder.Type.PURCHASE,
            status=PurchaseOrder.Status.ORDERED,
            invoice_number=validated_data.get("invoice_number"),
            notes=validated_data.get("notes"),
            discount=validated_data.get("discount", Decimal("0")),
            tax=validated_data.get("tax", Decimal("0")),
            subtotal=Decimal("0"),
            total_amount=Decimal("0"),
        )

        subtotal = Decimal("0")

        # 2. Create items
        for item in items_data:

            item_type = item["item_type"]
            item_id = item["item_id"]

            # 2.1 validate item existence
            if item_type == "ingredient":

                ingredient = get_object_or_404(
                    Ingredient,
                    id=item_id,
                    business=business,
                )

                resolved_id = ingredient.id

            elif item_type == "menu_item":

                menu_item = get_object_or_404(
                    MenuItem,
                    id=item_id,
                    business=business,
                )

                resolved_id = menu_item.id

            else:
                raise ValueError("Invalid item_type")

            # 3. calculate totals
            quantity = Decimal(str(item["quantity"]))
            unit_price = Decimal(str(item["unit_price"]))
            total = quantity * unit_price

            # 4. create item row
            PurchaseOrderItem.objects.create(
                purchase_order=po,
                item_type=item_type,
                item_id=resolved_id,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total,
            )

            subtotal += total

            # 5. stock update (ONLY for ingredient purchases)
            if item_type == "ingredient":
                ingredient.current_stock += quantity
                ingredient.save(update_fields=["current_stock"])

        # 6. final calculations
        discount = po.discount or Decimal("0")
        tax = po.tax or Decimal("0")

        po.subtotal = subtotal
        po.total_amount = subtotal - discount + tax

        po.save(update_fields=["subtotal", "total_amount"])

        return po

    @staticmethod
    @transaction.atomic
    def update_purchase_order(*, purchase_order, validated_data):

        items_data = validated_data.pop("items", None)

        # -------------------------
        # 1. update simple fields
        # -------------------------
        for key, value in validated_data.items():
            setattr(purchase_order, key, value)

        # -------------------------
        # 2. update items if provided
        # -------------------------
        if items_data is not None:

            # ⚠️ rollback stock changes (important for correctness)
            old_items = list(purchase_order.items.all())

            if purchase_order.type == PurchaseOrder.Type.PURCHASE:
                for old in old_items:
                    ingredient = Ingredient.objects.filter(
                        id=old.item_id,
                        business=purchase_order.business
                    ).first()

                    if ingredient:
                        ingredient.current_stock -= old.quantity
                        ingredient.save(update_fields=["current_stock"])

            # delete old items
            purchase_order.items.all().delete()

            subtotal = Decimal("0")

            for item in items_data:

                item_type = item["item_type"]
                item_id = item["item_id"]

                total = item["quantity"] * item["unit_price"]

                PurchaseOrderItem.objects.create(
                    purchase_order=purchase_order,
                    item_type=item_type,
                    item_id=item_id,
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    total_price=total,
                )

                subtotal += total

                # -------------------------
                # stock handling (only PURCHASE)
                # -------------------------
                if purchase_order.type == PurchaseOrder.Type.PURCHASE and item_type == "ingredient":
                    ingredient = get_object_or_404(
                        Ingredient,
                        id=item_id,
                        business=purchase_order.business,
                    )

                    ingredient.current_stock += item["quantity"]
                    ingredient.save(update_fields=["current_stock"])

            purchase_order.subtotal = subtotal

        # -------------------------
        # 3. recalc total
        # -------------------------
        purchase_order.total_amount = (
                purchase_order.subtotal
                - purchase_order.discount
                + purchase_order.tax
        )

        purchase_order.save()

        return purchase_order

    @staticmethod
    def delete_purchase_order(purchase_order):
        purchase_order.delete()

    @staticmethod
    def update_status(purchase_order, status):
        purchase_order.status = status
        purchase_order.save(update_fields=["status"])
        return purchase_order