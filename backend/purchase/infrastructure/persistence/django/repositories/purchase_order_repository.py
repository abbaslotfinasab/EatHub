from __future__ import annotations

from datetime import date

from django.db import transaction

from inventory.models import Ingredient
from purchase.domain.entities.purchase_order import PurchaseOrder
from purchase.domain.enums.purchase_order_status import PurchaseOrderStatus
from purchase.domain.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)
from purchase.infrastructure.persistence.django.mappers import (
    PurchaseOrderMapper,
)
from purchase.models import (
    PurchaseOrder as DjangoPurchaseOrder,
    PurchaseOrderItem as DjangoPurchaseOrderItem,
    PurchaseRequisition as DjangoPurchaseRequisition,
    Supplier as DjangoSupplier,
)


class DjangoPurchaseOrderRepository(PurchaseOrderRepository):
    @staticmethod
    def _aggregate_queryset():
        return DjangoPurchaseOrder.objects.select_related(
            "business",
            "supplier",
            "requisition",
        ).prefetch_related("items")

    def get_by_id_for_business(
        self,
        purchase_order_id: int,
        business_id: int,
    ) -> PurchaseOrder | None:
        model = self._aggregate_queryset().filter(
            id=purchase_order_id,
            business_id=business_id,
        ).first()

        if model is None:
            return None

        return PurchaseOrderMapper.to_domain(model)

    def get_by_id_for_business_for_update(
        self,
        purchase_order_id: int,
        business_id: int,
    ) -> PurchaseOrder | None:
        # Lock only the root row. The aggregate query may join nullable requisition.
        locked = DjangoPurchaseOrder.objects.select_for_update(of=("self",)).filter(
            id=purchase_order_id,
            business_id=business_id,
        ).exists()
        if not locked:
            return None

        model = self._aggregate_queryset().filter(
            id=purchase_order_id,
            business_id=business_id,
        ).first()
        return None if model is None else PurchaseOrderMapper.to_domain(model)

    def list(
        self,
        business_id: int,
        *,
        status: PurchaseOrderStatus | None = None,
        supplier_id: int | None = None,
        requisition_id: int | None = None,
        order_date_from: date | None = None,
        order_date_to: date | None = None,
    ) -> list[PurchaseOrder]:
        queryset = self._aggregate_queryset().filter(
            business_id=business_id,
        )

        if status is not None:
            queryset = queryset.filter(status=status)
        if supplier_id is not None:
            queryset = queryset.filter(supplier_id=supplier_id)
        if requisition_id is not None:
            queryset = queryset.filter(requisition_id=requisition_id)
        if order_date_from is not None:
            queryset = queryset.filter(order_date__gte=order_date_from)
        if order_date_to is not None:
            queryset = queryset.filter(order_date__lte=order_date_to)

        return [
            PurchaseOrderMapper.to_domain(model)
            for model in queryset.order_by("id")
        ]

    def exists_by_requisition(
        self,
        business_id: int,
        requisition_id: int,
    ) -> bool:
        return DjangoPurchaseOrder.objects.filter(
            business_id=business_id,
            requisition_id=requisition_id,
        ).exists()

    def save(self, purchase_order: PurchaseOrder) -> PurchaseOrder:
        with transaction.atomic():
            self._validate_cross_aggregate_ownership(purchase_order)

            if purchase_order.id is None:
                model = PurchaseOrderMapper.to_model(purchase_order)
                existing_items: list[DjangoPurchaseOrderItem] = []
            else:
                model = DjangoPurchaseOrder.objects.filter(
                    id=purchase_order.id,
                    business_id=purchase_order.business_id,
                ).first()
                if model is None:
                    raise ValueError(
                        "Purchase order does not exist in the specified business."
                    )

                created_at = model.created_at
                existing_items = list(
                    DjangoPurchaseOrderItem.objects.filter(
                        purchase_order=model,
                    ).order_by("id")
                )
                allowed = {
                    PurchaseOrderStatus.DRAFT.value: {
                        PurchaseOrderStatus.SENT.value,
                        PurchaseOrderStatus.CANCELLED.value,
                    },
                    PurchaseOrderStatus.SENT.value: {
                        PurchaseOrderStatus.PARTIAL.value,
                        PurchaseOrderStatus.RECEIVED.value,
                        PurchaseOrderStatus.CANCELLED.value,
                    },
                    PurchaseOrderStatus.PARTIAL.value: {
                        PurchaseOrderStatus.RECEIVED.value,
                        PurchaseOrderStatus.CANCELLED.value,
                    },
                    PurchaseOrderStatus.RECEIVED.value: set(),
                    PurchaseOrderStatus.CANCELLED.value: set(),
                }
                if (
                    purchase_order.status.value != model.status
                    and purchase_order.status.value not in allowed[model.status]
                ):
                    raise ValueError("Purchase order lifecycle transition is not allowed.")
                if model.status != PurchaseOrderStatus.DRAFT.value:
                    if not self._same_commercial_terms(model, existing_items, purchase_order):
                        raise ValueError(
                            "Purchase order terms and items cannot be changed after it is sent."
                        )
                model = PurchaseOrderMapper.to_model(purchase_order, model)
                model.created_at = created_at

            model.save()
            self._synchronize_items(model, purchase_order, existing_items)

            saved_model = self._aggregate_queryset().get(
                id=model.id,
                business_id=purchase_order.business_id,
            )

        return PurchaseOrderMapper.to_domain(saved_model)

    @staticmethod
    def _same_commercial_terms(model, existing_items, purchase_order: PurchaseOrder) -> bool:
        persisted_items = [
            (item.ingredient_id, item.quantity, item.unit_price)
            for item in existing_items
        ]
        proposed_items = [
            (item.ingredient_id, item.quantity, item.unit_price)
            for item in purchase_order.items
        ]
        return (
            model.supplier_id == purchase_order.supplier_id
            and model.requisition_id == purchase_order.requisition_id
            and model.order_date == purchase_order.order_date
            and model.expected_date == purchase_order.expected_date
            and model.discount == purchase_order.discount
            and model.tax == purchase_order.tax
            and persisted_items == proposed_items
        )

    @staticmethod
    def _synchronize_items(
        model: DjangoPurchaseOrder,
        purchase_order: PurchaseOrder,
        existing_items: list[DjangoPurchaseOrderItem],
    ) -> None:
        # Domain items do not expose a child identity, and duplicate
        # ingredients are valid. When the collection size is unchanged,
        # positional replacement updates the complete persisted collection
        # without treating ingredient_id as a key. When the size changes,
        # replace the collection as a whole so stale rows cannot survive.
        if len(existing_items) != len(purchase_order.items):
            DjangoPurchaseOrderItem.objects.filter(
                purchase_order=model,
            ).delete()
            for item in purchase_order.items:
                PurchaseOrderMapper.item_to_model(item, model).save()
            return

        for item_model, item in zip(existing_items, purchase_order.items):
            item_model.ingredient_id = item.ingredient_id
            item_model.quantity = item.quantity
            item_model.unit_price = item.unit_price
            item_model.save(
                update_fields=[
                    "ingredient",
                    "quantity",
                    "unit_price",
                    "updated_at",
                ]
            )

    @staticmethod
    def _validate_cross_aggregate_ownership(
        purchase_order: PurchaseOrder,
    ) -> None:
        if not DjangoSupplier.objects.filter(
            id=purchase_order.supplier_id,
            business_id=purchase_order.business_id,
        ).exists():
            raise ValueError(
                "Supplier does not exist in the purchase order business."
            )

        if purchase_order.requisition_id is not None and not (
            DjangoPurchaseRequisition.objects.filter(
                id=purchase_order.requisition_id,
                business_id=purchase_order.business_id,
            ).exists()
        ):
            raise ValueError(
                "Requisition does not exist in the purchase order business."
            )

        ingredient_ids = {
            item.ingredient_id for item in purchase_order.items
        }
        valid_ingredient_ids = set(
            Ingredient.objects.filter(
                id__in=ingredient_ids,
                business_id=purchase_order.business_id,
            ).values_list("id", flat=True)
        )
        if valid_ingredient_ids != ingredient_ids:
            raise ValueError(
                "All purchase order ingredients must belong to the purchase order business."
            )
