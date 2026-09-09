from django.db import transaction

from inventory.models import Ingredient
from purchase.domain.entities.requisition import PurchaseRequisition
from purchase.domain.enums.requisition_status import RequisitionStatus
from purchase.domain.repositories.requisition_repository import (
    RequisitionRepository,
)
from purchase.infrastructure.persistence.django.mappers import (
    PurchaseRequisitionMapper,
)
from purchase.models import (
    PurchaseRequisition as DjangoPurchaseRequisition,
    PurchaseRequisitionItem as DjangoPurchaseRequisitionItem,
)


class DjangoRequisitionRepository(RequisitionRepository):
    @staticmethod
    def _aggregate_queryset():
        return DjangoPurchaseRequisition.objects.select_related(
            "business",
            "requested_by",
        ).prefetch_related("items")

    def get_by_id_for_business(
        self,
        requisition_id: int,
        business_id: int,
    ) -> PurchaseRequisition | None:
        model = self._aggregate_queryset().filter(
            id=requisition_id,
            business_id=business_id,
        ).first()

        if model is None:
            return None

        return PurchaseRequisitionMapper.to_domain(model)

    def list(
        self,
        business_id: int,
        *,
        status: RequisitionStatus | None = None,
        requested_by_id: int | None = None,
    ) -> list[PurchaseRequisition]:
        queryset = self._aggregate_queryset().filter(
            business_id=business_id,
        )

        if status is not None:
            queryset = queryset.filter(status=status)

        if requested_by_id is not None:
            queryset = queryset.filter(requested_by_id=requested_by_id)

        return [
            PurchaseRequisitionMapper.to_domain(model)
            for model in queryset.order_by("id")
        ]

    def save(
        self,
        requisition: PurchaseRequisition,
    ) -> PurchaseRequisition:
        with transaction.atomic():
            self._ensure_item_ingredients_belong_to_business(requisition)

            if requisition.id is None:
                model = PurchaseRequisitionMapper.to_model(requisition)
            else:
                model = DjangoPurchaseRequisition.objects.filter(
                    id=requisition.id,
                    business_id=requisition.business_id,
                ).first()

                if model is None:
                    raise ValueError(
                        "Purchase requisition does not exist in the specified business."
                    )

                if model.business_id != requisition.business_id:
                    raise ValueError("Purchase requisition business cannot be changed.")

                created_at = model.created_at
                model = PurchaseRequisitionMapper.to_model(requisition, model)
                model.created_at = created_at

            model.save()

            DjangoPurchaseRequisitionItem.objects.filter(
                requisition=model,
            ).delete()
            DjangoPurchaseRequisitionItem.objects.bulk_create([
                PurchaseRequisitionMapper.item_to_model(item, model)
                for item in requisition.items
            ])

            saved_model = self._aggregate_queryset().get(
                id=model.id,
                business_id=requisition.business_id,
            )

        return PurchaseRequisitionMapper.to_domain(saved_model)

    @staticmethod
    def _ensure_item_ingredients_belong_to_business(
        requisition: PurchaseRequisition,
    ) -> None:
        ingredient_ids = {item.ingredient_id for item in requisition.items}
        valid_ingredient_ids = set(
            Ingredient.objects.filter(
                business_id=requisition.business_id,
                id__in=ingredient_ids,
            ).values_list("id", flat=True)
        )

        if valid_ingredient_ids != ingredient_ids:
            raise ValueError(
                "All requisition ingredients must belong to the requisition business."
            )
