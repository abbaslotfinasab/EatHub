from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.db.models import Prefetch, Sum

from inventory.models import Ingredient
from purchase.domain.entities.goods_receipt import GoodsReceipt
from purchase.domain.repositories.goods_receipt_repository import (
    GoodsReceiptRepository,
)
from purchase.infrastructure.persistence.django.mappers import (
    GoodsReceiptMapper,
)
from purchase.models import (
    GoodsReceipt as DjangoGoodsReceipt,
    GoodsReceiptItem as DjangoGoodsReceiptItem,
    PurchaseOrder as DjangoPurchaseOrder,
    PurchaseOrderItem as DjangoPurchaseOrderItem,
)


class DjangoGoodsReceiptRepository(GoodsReceiptRepository):
    @staticmethod
    def _aggregate_queryset():
        item_queryset = DjangoGoodsReceiptItem.objects.select_related(
            "purchase_order_item",
            "purchase_order_item__ingredient",
        )
        return DjangoGoodsReceipt.objects.select_related(
            "business",
            "purchase_order",
            "received_by",
        ).prefetch_related(
            Prefetch("items", queryset=item_queryset),
        )

    def get_by_id_for_business(
        self,
        goods_receipt_id: int,
        business_id: int,
    ) -> GoodsReceipt | None:
        model = self._aggregate_queryset().filter(
            id=goods_receipt_id,
            business_id=business_id,
        ).first()

        if model is None:
            return None

        return GoodsReceiptMapper.to_domain(model)

    def list(
        self,
        business_id: int,
        *,
        purchase_order_id: int | None = None,
        received_by_id: int | None = None,
        received_from: datetime | None = None,
        received_to: datetime | None = None,
    ) -> list[GoodsReceipt]:
        queryset = self._aggregate_queryset().filter(
            business_id=business_id,
        )

        if purchase_order_id is not None:
            queryset = queryset.filter(purchase_order_id=purchase_order_id)
        if received_by_id is not None:
            queryset = queryset.filter(received_by_id=received_by_id)
        if received_from is not None:
            queryset = queryset.filter(received_date__gte=received_from)
        if received_to is not None:
            queryset = queryset.filter(received_date__lte=received_to)

        return [
            GoodsReceiptMapper.to_domain(model)
            for model in queryset.order_by("id")
        ]

    def received_quantities_for_purchase_order(
        self,
        business_id: int,
        purchase_order_id: int,
    ) -> dict[int, Decimal]:
        rows = (
            DjangoGoodsReceiptItem.objects.filter(
                receipt__business_id=business_id,
                receipt__purchase_order_id=purchase_order_id,
            )
            .values("purchase_order_item_id")
            .annotate(received=Sum("received_quantity"))
        )
        return {
            row["purchase_order_item_id"]: row["received"] or Decimal("0")
            for row in rows
        }

    def save(self, goods_receipt: GoodsReceipt) -> GoodsReceipt:
        with transaction.atomic():
            goods_receipt.validate()
            if goods_receipt.id is not None:
                raise ValueError("Goods receipts are immutable once created.")
            self._validate_cross_aggregate_ownership(goods_receipt)

            if goods_receipt.id is None:
                model = GoodsReceiptMapper.to_model(goods_receipt)
                existing_items: list[DjangoGoodsReceiptItem] = []

            model.save()
            self._synchronize_items(model, goods_receipt, existing_items)

            saved_model = self._aggregate_queryset().get(
                id=model.id,
                business_id=goods_receipt.business_id,
            )

        return GoodsReceiptMapper.to_domain(saved_model)

    @staticmethod
    def _synchronize_items(
        model: DjangoGoodsReceipt,
        goods_receipt: GoodsReceipt,
        existing_items: list[DjangoGoodsReceiptItem],
    ) -> None:
        for index, item in enumerate(goods_receipt.items):
            if index < len(existing_items):
                item_model = existing_items[index]
                item_model.purchase_order_item_id = item.purchase_order_item_id
                item_model.received_quantity = item.received_quantity
                item_model.rejected_quantity = item.rejected_quantity
                item_model.save(
                    update_fields=[
                        "purchase_order_item",
                        "received_quantity",
                        "rejected_quantity",
                        "updated_at",
                    ]
                )
            else:
                GoodsReceiptMapper.item_to_model(item, model).save()

        if len(existing_items) > len(goods_receipt.items):
            DjangoGoodsReceiptItem.objects.filter(
                id__in=[
                    item.id for item in existing_items[len(goods_receipt.items):]
                ],
            ).delete()

    @staticmethod
    def _validate_cross_aggregate_ownership(
        goods_receipt: GoodsReceipt,
    ) -> None:
        purchase_order = DjangoPurchaseOrder.objects.filter(
            id=goods_receipt.purchase_order_id,
            business_id=goods_receipt.business_id,
        ).first()
        if purchase_order is None:
            raise ValueError(
                "Purchase order does not exist in the goods receipt business."
            )

        item_ids = {
            item.purchase_order_item_id for item in goods_receipt.items
        }
        valid_items = DjangoPurchaseOrderItem.objects.filter(
            id__in=item_ids,
            purchase_order_id=purchase_order.id,
            purchase_order__business_id=goods_receipt.business_id,
        )
        valid_item_rows = list(
            valid_items.values("id", "ingredient_id")
        )
        if {row["id"] for row in valid_item_rows} != item_ids:
            raise ValueError(
                "All goods receipt items must belong to its purchase order."
            )

        ingredient_ids = {row["ingredient_id"] for row in valid_item_rows}
        valid_ingredient_ids = set(
            Ingredient.objects.filter(
                id__in=ingredient_ids,
                business_id=goods_receipt.business_id,
            ).values_list("id", flat=True)
        )
        if valid_ingredient_ids != ingredient_ids:
            raise ValueError(
                "All goods receipt ingredients must belong to its business."
            )
