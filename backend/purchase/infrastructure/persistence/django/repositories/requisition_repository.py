import builtins
import sqlite3

from django.db import IntegrityError, OperationalError, transaction

from purchase.domain.entities.requisition import (
    PurchaseRequisition,
    PurchaseRequisitionDecision as PurchaseRequisitionDecisionEntity,
)
from purchase.domain.enums.requisition_status import RequisitionStatus
from purchase.domain.repositories.requisition_repository import (
    RequisitionRepository,
)
from purchase.infrastructure.persistence.django.mappers import (
    PurchaseRequisitionDecisionMapper,
    PurchaseRequisitionMapper,
)
from purchase.models import (
    PurchaseRequisition as DjangoPurchaseRequisition,
    PurchaseRequisitionDecision,
    PurchaseRequisitionItem as DjangoPurchaseRequisitionItem,
)


_POSTGRES_DECISION_CONFLICT_SQLSTATES = frozenset(
    {
        "40001",  # serialization_failure
        "40P01",  # deadlock_detected
        "55P03",  # lock_not_available, including lock_timeout
    }
)
_POSTGRES_UNIQUE_VIOLATION_SQLSTATE = "23505"
_DECISION_UNIQUE_CONSTRAINT = "pur_req_decision_uq"


def _exception_causes(error: Exception):
    """Yield the explicit cause chain without consulting implicit context."""
    current = error
    seen = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = current.__cause__


def _is_supported_decision_conflict(error: OperationalError) -> bool:
    """Recognize only documented lock/serialization codes for configured DBs.

    EatHub configures SQLite and PostgreSQL. Django wraps driver exceptions in
    ``__cause__``; psycopg2 exposes SQLSTATE as ``pgcode`` and SQLite exposes
    primary/extended result codes as ``sqlite_errorcode``.
    """
    for current in _exception_causes(error):
        sqlstate = getattr(current, "sqlstate", None) or getattr(
            current, "pgcode", None
        )
        if sqlstate is None:
            sqlstate = getattr(getattr(current, "diag", None), "sqlstate", None)
        if sqlstate in _POSTGRES_DECISION_CONFLICT_SQLSTATES:
            return True

        sqlite_errorcode = getattr(current, "sqlite_errorcode", None)
        if isinstance(sqlite_errorcode, int) and (
            sqlite_errorcode & 0xFF
        ) in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
            return True

    return False


def _is_expected_decision_integrity_conflict(error: IntegrityError) -> bool:
    """Recognize only the requisition-decision uniqueness invariant."""
    for current in _exception_causes(error):
        sqlstate = getattr(current, "sqlstate", None) or getattr(
            current, "pgcode", None
        )
        if sqlstate == _POSTGRES_UNIQUE_VIOLATION_SQLSTATE:
            constraint_name = getattr(
                getattr(current, "diag", None), "constraint_name", None
            )
            if constraint_name == _DECISION_UNIQUE_CONSTRAINT:
                return True

        sqlite_errorcode = getattr(current, "sqlite_errorcode", None)
        if sqlite_errorcode == getattr(sqlite3, "SQLITE_CONSTRAINT_UNIQUE", None):
            return True

    return False


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
            self._ensure_item_ingredients_belong_to_business(
                model,
                requisition.business_id,
                {item.ingredient_id for item in requisition.items},
            )

            saved_model = self._aggregate_queryset().get(
                id=model.id,
                business_id=requisition.business_id,
            )

        return PurchaseRequisitionMapper.to_domain(saved_model)

    def record_decision(
        self,
        requisition_id: int,
        business_id: int,
        actor_id: int,
        decision: str,
        rejection_reason: str | None = None,
    ) -> PurchaseRequisition:
        try:
            with transaction.atomic():
                model = (
                    DjangoPurchaseRequisition.objects.select_for_update()
                    .filter(id=requisition_id, business_id=business_id)
                    .first()
                )
                if model is None:
                    raise ValueError(
                        "Requisition does not exist in this business."
                    )

                entity = PurchaseRequisitionMapper.to_domain(model)
                if decision == PurchaseRequisitionDecision.Decision.APPROVED:
                    entity.approve(actor_id)
                elif decision == PurchaseRequisitionDecision.Decision.REJECTED:
                    entity.reject()
                else:
                    raise ValueError("Unsupported requisition decision.")

                model.status = entity.status
                model.save(update_fields=["status", "updated_at"])
                PurchaseRequisitionDecision.objects.create(
                    requisition=model,
                    decision=decision,
                    actor_id=actor_id,
                    previous_status=DjangoPurchaseRequisition.Status.SUBMITTED,
                    resulting_status=entity.status,
                    rejection_reason=(
                        rejection_reason
                        if decision == PurchaseRequisitionDecision.Decision.REJECTED
                        else None
                    ),
                )
                saved_model = self._aggregate_queryset().get(
                    id=model.id,
                    business_id=business_id,
                )
        except IntegrityError as error:
            if _is_expected_decision_integrity_conflict(error):
                raise ValueError(
                    "The requisition decision conflicts with the current record."
                ) from error
            raise
        except OperationalError as error:
            if _is_supported_decision_conflict(error):
                raise ValueError(
                    "The requisition decision conflicted with another update."
                ) from error
            raise

        return PurchaseRequisitionMapper.to_domain(saved_model)

    def list_decisions_for_business(
        self,
        requisition_id: int,
        business_id: int,
    ) -> builtins.list[PurchaseRequisitionDecisionEntity]:
        models = (
            PurchaseRequisitionDecision.objects.filter(
                requisition_id=requisition_id,
                requisition__business_id=business_id,
            )
            .select_related("actor")
            .order_by("decided_at", "id")
        )
        return [PurchaseRequisitionDecisionMapper.to_domain(model) for model in models]

    @staticmethod
    def _ensure_item_ingredients_belong_to_business(
        model: DjangoPurchaseRequisition,
        business_id: int,
        ingredient_ids: set[int],
    ) -> None:
        valid_ingredient_ids = set(DjangoPurchaseRequisitionItem.objects.filter(
            requisition=model,
            ingredient_id__in=ingredient_ids,
            ingredient__business_id=business_id,
        ).values_list("ingredient_id", flat=True))

        if valid_ingredient_ids != ingredient_ids:
            raise ValueError(
                "All requisition ingredients must belong to the requisition business."
            )
