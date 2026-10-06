from datetime import date
from django.db import transaction
from django.db.models import Prefetch

from inventory.models import Ingredient
from purchase.domain.entities.purchase_invoice import PurchaseInvoice
from purchase.domain.enums.purchase_invoice_status import PurchaseInvoiceStatus
from purchase.domain.repositories.purchase_invoice_repository import PurchaseInvoiceRepository
from purchase.infrastructure.persistence.django.mappers import PurchaseInvoiceMapper
from purchase.models import (
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

    def lock_for_posting(self, business_id: int, purchase_invoice_id: int) -> bool:
        # Lock only the invoice row. Load nullable relations after this query.
        return DjangoPurchaseInvoice.objects.select_for_update(of=("self",)).filter(
            id=purchase_invoice_id,
            business_id=business_id,
        ).exists()

    def save_posted(self, purchase_invoice: PurchaseInvoice) -> PurchaseInvoice:
        purchase_invoice.validate()
        if purchase_invoice.status != PurchaseInvoiceStatus.POSTED:
            raise ValueError("Purchase invoice must be posted before persistence.")
        model = DjangoPurchaseInvoice.objects.select_for_update(of=("self",)).filter(
            id=purchase_invoice.id,
            business_id=purchase_invoice.business_id,
            status=PurchaseInvoiceStatus.APPROVED.value,
        ).first()
        if model is None:
            raise ValueError("Only an approved purchase invoice can be posted.")
        model.status = PurchaseInvoiceStatus.POSTED.value
        model.posted_at = purchase_invoice.posted_at
        model.posted_by_id = purchase_invoice.posted_by_id
        model.save(update_fields=["status", "posted_at", "posted_by", "updated_at"])
        saved = self._aggregate_queryset().get(
            id=model.id,
            business_id=purchase_invoice.business_id,
        )
        return PurchaseInvoiceMapper.to_domain(saved)

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

    def save(self, purchase_invoice: PurchaseInvoice) -> PurchaseInvoice:
        with transaction.atomic():
            purchase_invoice.validate()
            self._validate_cross_aggregate_ownership(purchase_invoice)
            if self.exists_by_number(
                purchase_invoice.business_id, purchase_invoice.supplier_id,
                purchase_invoice.invoice_number, exclude_id=purchase_invoice.id,
            ):
                raise ValueError("Invoice number already exists in this business.")

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
                if purchase_invoice.status == PurchaseInvoiceStatus.POSTED:
                    raise ValueError("Posted invoices must use the atomic posting workflow.")
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
            item_model.purchase_order_item_id = item.purchase_order_item_id
            item_model.description = item.description
            item_model.quantity = item.quantity
            item_model.unit_price = item.unit_price
            item_model.discount_percent = item.discount_percent
            item_model.discount_amount = item.discount_amount
            item_model.tax_percent = item.tax_percent
            item_model.tax_amount = item.tax_amount
            item_model.total_price = item.total_price
            item_model.save(update_fields=[
                "ingredient", "purchase_order_item", "description", "quantity", "unit_price",
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
        po_item_ids = {item.purchase_order_item_id for item in invoice.items}
        po_items = {
            item.id: item
            for item in DjangoPurchaseOrderItem.objects.select_related("ingredient").filter(
                id__in=po_item_ids,
                purchase_order_id=order.id,
                purchase_order__business_id=invoice.business_id,
            )
        }
        if set(po_items) != po_item_ids:
            raise ValueError("Purchase order item does not belong to this purchase order and business.")
        invoice.validate_purchase_order_item_references(
            purchase_order_id=order.id,
            purchase_order_business_id=order.business_id,
            item_ingredient_ids={po_item.id: po_item.ingredient_id for po_item in po_items.values()},
        )
        for item in invoice.items:
            po_item = po_items[item.purchase_order_item_id]
            if po_item.ingredient.business_id != invoice.business_id:
                raise ValueError("Purchase order item ingredient does not belong to the invoice business.")
