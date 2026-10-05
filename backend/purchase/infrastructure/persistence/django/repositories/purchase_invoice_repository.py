from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Prefetch, Sum

from inventory.models import Ingredient
from purchase.domain.entities.purchase_invoice import PurchaseInvoice
from purchase.domain.enums.purchase_invoice_status import PurchaseInvoiceStatus
from purchase.domain.repositories.purchase_invoice_repository import PurchaseInvoiceRepository
from purchase.infrastructure.persistence.django.mappers import PurchaseInvoiceMapper
from purchase.models import (
    GoodsReceiptItem as DjangoGoodsReceiptItem,
    PurchaseInvoice as DjangoPurchaseInvoice,
    PurchaseInvoiceItem as DjangoPurchaseInvoiceItem,
    PurchaseOrder as DjangoPurchaseOrder,
    PurchaseOrderItem as DjangoPurchaseOrderItem,
    Supplier as DjangoSupplier,
)


class DjangoPurchaseInvoiceRepository(PurchaseInvoiceRepository):
    @staticmethod
    def _aggregate_queryset():
        return DjangoPurchaseInvoice.objects.select_related(
            "business", "supplier", "purchase_order",
        ).prefetch_related(
            Prefetch("items", queryset=DjangoPurchaseInvoiceItem.objects.order_by("id")),
        )

    def get_by_id_for_business(self, purchase_invoice_id: int, business_id: int):
        model = self._aggregate_queryset().filter(
            id=purchase_invoice_id, business_id=business_id,
        ).first()
        return None if model is None else PurchaseInvoiceMapper.to_domain(model)

    def list(self, business_id: int, *, supplier_id: int | None = None,
             purchase_order_id: int | None = None,
             invoice_date_from: date | None = None,
             invoice_date_to: date | None = None) -> list[PurchaseInvoice]:
        qs = self._aggregate_queryset().filter(business_id=business_id)
        if supplier_id is not None:
            qs = qs.filter(supplier_id=supplier_id)
        if purchase_order_id is not None:
            qs = qs.filter(purchase_order_id=purchase_order_id)
        if invoice_date_from is not None:
            qs = qs.filter(invoice_date__gte=invoice_date_from)
        if invoice_date_to is not None:
            qs = qs.filter(invoice_date__lte=invoice_date_to)
        return [PurchaseInvoiceMapper.to_domain(m) for m in qs.order_by("id")]

    def exists_by_number(self, business_id: int, supplier_id: int,
                         invoice_number: str, *, exclude_id: int | None = None) -> bool:
        qs = DjangoPurchaseInvoice.objects.filter(
            business_id=business_id, invoice_number=invoice_number,
        )
        if exclude_id is not None:
            qs = qs.exclude(id=exclude_id)
        return qs.exists()

    def accepted_received_quantities(self, business_id: int, purchase_order_id: int):
        rows = DjangoGoodsReceiptItem.objects.filter(
            receipt__business_id=business_id,
            receipt__purchase_order_id=purchase_order_id,
        ).values("purchase_order_item__ingredient_id").annotate(
            quantity=Sum("received_quantity"),
        )
        return {row["purchase_order_item__ingredient_id"]: row["quantity"] or Decimal("0") for row in rows}

    def previously_invoiced_quantities(self, business_id: int, purchase_order_id: int,
                                       *, exclude_id: int | None = None):
        qs = DjangoPurchaseInvoiceItem.objects.filter(
            purchase_invoice__business_id=business_id,
            purchase_invoice__purchase_order_id=purchase_order_id,
        )
        if exclude_id is not None:
            qs = qs.exclude(purchase_invoice_id=exclude_id)
        rows = qs.values("ingredient_id").annotate(quantity=Sum("quantity"))
        return {row["ingredient_id"]: row["quantity"] or Decimal("0") for row in rows}

    def save(self, purchase_invoice: PurchaseInvoice) -> PurchaseInvoice:
        with transaction.atomic():
            purchase_invoice.validate()
            self._validate_cross_aggregate_ownership(purchase_invoice)
            if self.exists_by_number(
                purchase_invoice.business_id, purchase_invoice.supplier_id,
                purchase_invoice.invoice_number, exclude_id=purchase_invoice.id,
            ):
                raise ValueError("Invoice number already exists in this business.")
            self._validate_invoiceable_quantities(purchase_invoice)

            if purchase_invoice.id is None:
                if purchase_invoice.status != PurchaseInvoiceStatus.DRAFT:
                    raise ValueError("New purchase invoices must start as drafts.")
                model = PurchaseInvoiceMapper.to_model(purchase_invoice)
                existing = []
            else:
                model = DjangoPurchaseInvoice.objects.select_for_update().filter(
                    id=purchase_invoice.id, business_id=purchase_invoice.business_id,
                ).first()
                if model is None:
                    raise ValueError("Purchase invoice does not exist in the specified business.")
                if model.status != PurchaseInvoiceStatus.DRAFT.value:
                    raise ValueError("Approved purchase invoice cannot be modified.")
                created_at = model.created_at
                existing = list(DjangoPurchaseInvoiceItem.objects.filter(
                    purchase_invoice=model,
                ).order_by("id"))
                model = PurchaseInvoiceMapper.to_model(purchase_invoice, model)
                model.created_at = created_at
            model.save()
            self._synchronize_items(model, purchase_invoice, existing)
            saved = self._aggregate_queryset().get(
                id=model.id, business_id=purchase_invoice.business_id,
            )
        return PurchaseInvoiceMapper.to_domain(saved)

    @staticmethod
    def _synchronize_items(model, invoice, existing) -> None:
        if len(existing) != len(invoice.items):
            DjangoPurchaseInvoiceItem.objects.filter(purchase_invoice=model).delete()
            for item in invoice.items:
                PurchaseInvoiceMapper.item_to_model(item, model).save()
            return
        for item_model, item in zip(existing, invoice.items):
            item_model.ingredient_id = item.ingredient_id
            item_model.description = item.description
            item_model.quantity = item.quantity
            item_model.unit_price = item.unit_price
            item_model.discount_percent = item.discount_percent
            item_model.discount_amount = item.discount_amount
            item_model.tax_percent = item.tax_percent
            item_model.tax_amount = item.tax_amount
            item_model.total_price = item.total_price
            item_model.save(update_fields=[
                "ingredient", "description", "quantity", "unit_price",
                "discount_percent", "discount_amount", "tax_percent",
                "tax_amount", "total_price", "updated_at",
            ])

    @staticmethod
    def _validate_cross_aggregate_ownership(invoice: PurchaseInvoice) -> None:
        supplier = DjangoSupplier.objects.filter(
            id=invoice.supplier_id, business_id=invoice.business_id,
        ).first()
        if supplier is None:
            raise ValueError("Supplier does not exist in the invoice business.")
        order = DjangoPurchaseOrder.objects.filter(
            id=invoice.purchase_order_id, business_id=invoice.business_id,
        ).first()
        if order is None:
            raise ValueError("Purchase order does not exist in the invoice business.")
        if order.supplier_id != invoice.supplier_id:
            raise ValueError("Purchase order supplier does not match invoice supplier.")
        ingredient_ids = {item.ingredient_id for item in invoice.items}
        valid = set(Ingredient.objects.filter(
            id__in=ingredient_ids, business_id=invoice.business_id,
        ).values_list("id", flat=True))
        if valid != ingredient_ids:
            raise ValueError("All invoice ingredients must belong to the invoice business.")
        order_ingredients = set(DjangoPurchaseOrderItem.objects.filter(
            purchase_order=order, ingredient_id__in=ingredient_ids,
        ).values_list("ingredient_id", flat=True))
        if order_ingredients != ingredient_ids:
            raise ValueError("All invoice ingredients must belong to the purchase order.")

    def _validate_invoiceable_quantities(self, invoice: PurchaseInvoice) -> None:
        received = self.accepted_received_quantities(invoice.business_id, invoice.purchase_order_id)
        invoiced = self.previously_invoiced_quantities(
            invoice.business_id, invoice.purchase_order_id, exclude_id=invoice.id,
        )
        requested = {}
        for item in invoice.items:
            requested[item.ingredient_id] = requested.get(item.ingredient_id, Decimal("0")) + item.quantity
        # No receipt means the invoice remains representable as unmatched.
        if not received:
            return
        for ingredient_id, quantity in requested.items():
            available = received.get(ingredient_id, Decimal("0")) - invoiced.get(ingredient_id, Decimal("0"))
            if quantity > available:
                raise ValueError("Invoice quantity cannot exceed accepted received quantity.")
