from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from django.db import transaction

from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.views import TenantAPIView
from core.enums import PermissionCode
from purchase.application.dto.purchase_invoice import (
    ApprovePurchaseInvoiceDTO,
    CancelPurchaseInvoiceDTO,
    CreatePurchaseInvoiceDTO,
    CreatePurchaseInvoiceItemDTO,
    ListPurchaseInvoicesQuery,
    UpdatePurchaseInvoiceDTO,
)
from purchase.application.dto.purchase_invoice_posting import PostPurchaseInvoiceDTO
from purchase.application.use_cases.purchase_invoice.approve_purchase_invoice import ApprovePurchaseInvoiceUseCase
from purchase.application.use_cases.purchase_invoice.create_purchase_invoice import CreatePurchaseInvoiceUseCase
from purchase.application.use_cases.purchase_invoice.cancel_purchase_invoice import CancelPurchaseInvoice
from purchase.application.use_cases.purchase_invoice.get_purchase_invoice import GetPurchaseInvoiceUseCase
from purchase.application.use_cases.purchase_invoice.list_purchase_invoices import ListPurchaseInvoicesUseCase
from purchase.application.use_cases.purchase_invoice.match_purchase_invoice import MatchPurchaseInvoiceUseCase
from purchase.application.use_cases.purchase_invoice.post_purchase_invoice import PostPurchaseInvoice
from purchase.application.use_cases.purchase_invoice.update_purchase_invoice import UpdatePurchaseInvoiceUseCase
from purchase.infrastructure.persistence.transaction import DjangoTransactionManager
from purchase.infrastructure.persistence.django.repositories.purchase_invoice_repository import DjangoPurchaseInvoiceRepository
from purchase.infrastructure.persistence.django.repositories.purchase_invoice_matching_repository import DjangoPurchaseInvoiceMatchingRepository
from purchase.infrastructure.persistence.django.repositories.accounts_payable_repository import DjangoAccountsPayableRepository
from purchase.presentation.api.serializers.purchase_invoice import (
    CreatePurchaseInvoiceSerializer,
    PurchaseInvoiceSerializer,
    PurchaseInvoiceMatchResponseSerializer,
    UpdatePurchaseInvoiceSerializer,
)
from purchase.presentation.api.serializers.purchase_invoice_posting import (
    PostPurchaseInvoiceRequestSerializer,
    PostPurchaseInvoiceResponseSerializer,
)
from purchase.presentation.api.permissions import require_purchase_permission
from purchase.models import PurchaseInvoiceEvent
from purchase.presentation.api.serializers.purchase_invoice_event import PurchaseInvoiceEventSerializer


def _repository() -> DjangoPurchaseInvoiceRepository:
    return DjangoPurchaseInvoiceRepository()


def _transaction_manager() -> DjangoTransactionManager:
    return DjangoTransactionManager()


def _matching_use_case() -> MatchPurchaseInvoiceUseCase:
    return MatchPurchaseInvoiceUseCase(
        DjangoPurchaseInvoiceMatchingRepository(),
        _transaction_manager(),
    )


def _posting_use_case() -> PostPurchaseInvoice:
    transaction_manager = _transaction_manager()
    return PostPurchaseInvoice(
        _repository(),
        DjangoAccountsPayableRepository(),
        MatchPurchaseInvoiceUseCase(
            DjangoPurchaseInvoiceMatchingRepository(),
            transaction_manager,
        ),
        transaction_manager,
    )


def _optional_id(value: str | None, name: str) -> int | None:
    if value in (None, ""):
        return None
    try:
        result = int(value)
    except ValueError as error:
        raise ValidationError({name: "Must be a valid integer."}) from error
    if result <= 0:
        raise ValidationError({name: "Must be a positive integer."})
    return result


def _optional_date(value: str | None, name: str) -> date | None:
    if value in (None, ""):
        return None
    try:
        return serializers.DateField().to_internal_value(value)
    except ValidationError as error:
        raise ValidationError({name: error.detail}) from error


def _handle(error: ValueError) -> None:
    detail = str(error)
    if "does not exist" in detail:
        raise NotFound({"detail": detail})
    raise ValidationError({"detail": detail})


def _json_safe(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "items") and not isinstance(value, (str, bytes)):
        return {str(key): _json_safe(item) for key, item in value.items()}
    return value


def _invoice_snapshot(invoice):
    return _json_safe({
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


def _record_invoice_event(
    invoice, actor, event_type, *, previous_status=None, metadata=None,
):
    return PurchaseInvoiceEvent.objects.create(
        business_id=invoice.business_id,
        purchase_invoice_id=invoice.id,
        actor=actor,
        event_type=event_type,
        previous_status=getattr(previous_status, "value", previous_status),
        resulting_status=getattr(invoice.status, "value", invoice.status),
        metadata=_json_safe(metadata or {}),
    )


class PurchaseInvoiceEventListAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        require_purchase_permission(request, PermissionCode.PURCHASE_VIEW)
        if not _repository().get_by_id_for_business(pk, request.business.id):
            raise NotFound({"detail": "Purchase invoice does not exist in this business."})
        events = PurchaseInvoiceEvent.objects.filter(
            business_id=request.business.id,
            purchase_invoice_id=pk,
        ).select_related("actor").order_by("occurred_at", "id")
        return Response(PurchaseInvoiceEventSerializer(events, many=True).data)


class PurchaseInvoiceListCreateAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        require_purchase_permission(request, PermissionCode.PURCHASE_VIEW)
        try:
            result = ListPurchaseInvoicesUseCase(_repository()).execute(
                ListPurchaseInvoicesQuery(
                    business_id=request.business.id,
                    supplier_id=_optional_id(request.query_params.get("supplier_id"), "supplier_id"),
                    purchase_order_id=_optional_id(request.query_params.get("purchase_order_id"), "purchase_order_id"),
                    invoice_date_from=_optional_date(request.query_params.get("invoice_date_from"), "invoice_date_from"),
                    invoice_date_to=_optional_date(request.query_params.get("invoice_date_to"), "invoice_date_to"),
                )
            )
        except ValueError as error:
            _handle(error)
        return Response(PurchaseInvoiceSerializer(result, many=True).data)

    def post(self, request):
        require_purchase_permission(request, PermissionCode.PURCHASE_INVOICE_CREATE)
        serializer = CreatePurchaseInvoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            with transaction.atomic():
                result = CreatePurchaseInvoiceUseCase(_repository()).execute(
                    CreatePurchaseInvoiceDTO(
                        business_id=request.business.id,
                        supplier_id=data["supplier_id"],
                        purchase_order_id=data["purchase_order_id"],
                        invoice_number=data["invoice_number"],
                        invoice_date=data["invoice_date"],
                        discount_percent=data["discount_percent"],
                        tax_percent=data["tax_percent"],
                        items=[CreatePurchaseInvoiceItemDTO(**item) for item in data["items"]],
                    )
                )
                _record_invoice_event(
                    result, request.user, PurchaseInvoiceEvent.EventType.CREATED,
                    metadata={"after": _invoice_snapshot(result)},
                )
        except ValueError as error:
            _handle(error)
        return Response(PurchaseInvoiceSerializer(result).data, status=status.HTTP_201_CREATED)


class PurchaseInvoiceDetailAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        require_purchase_permission(request, PermissionCode.PURCHASE_VIEW)
        try:
            result = GetPurchaseInvoiceUseCase(_repository()).execute(pk, request.business.id)
        except ValueError as error:
            _handle(error)
        return Response(PurchaseInvoiceSerializer(result).data)

    def put(self, request, pk):
        require_purchase_permission(request, PermissionCode.PURCHASE_INVOICE_UPDATE)
        serializer = UpdatePurchaseInvoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            with transaction.atomic():
                repository = _repository()
                before = repository.get_by_id_for_business(pk, request.business.id)
                result = UpdatePurchaseInvoiceUseCase(repository).execute(
                    UpdatePurchaseInvoiceDTO(
                        business_id=request.business.id,
                        purchase_invoice_id=pk,
                        supplier_id=data["supplier_id"],
                        purchase_order_id=data["purchase_order_id"],
                        invoice_number=data["invoice_number"],
                        invoice_date=data["invoice_date"],
                        discount_percent=data["discount_percent"],
                        tax_percent=data["tax_percent"],
                        items=[
                            CreatePurchaseInvoiceItemDTO(**item)
                            for item in data["items"]
                        ],
                    )
                )
                _record_invoice_event(
                    result, request.user, PurchaseInvoiceEvent.EventType.UPDATED,
                    previous_status=before.status if before else None,
                    metadata={
                        "before": _invoice_snapshot(before) if before else None,
                        "after": _invoice_snapshot(result),
                    },
                )
        except ValueError as error:
            _handle(error)
        return Response(PurchaseInvoiceSerializer(result).data)


class PurchaseInvoiceApproveAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        require_purchase_permission(request, PermissionCode.PURCHASE_INVOICE_APPROVE)
        try:
            with transaction.atomic():
                repository = _repository()
                before = repository.get_by_id_for_business(pk, request.business.id)
                result = ApprovePurchaseInvoiceUseCase(
                    repository,
                    _transaction_manager(),
                ).execute(
                    ApprovePurchaseInvoiceDTO(
                        business_id=request.business.id,
                        purchase_invoice_id=pk,
                        approved_by_id=request.user.id,
                        approved_at=timezone.now(),
                    )
                )
                _record_invoice_event(
                    result, request.user, PurchaseInvoiceEvent.EventType.APPROVED,
                    previous_status=before.status if before else None,
                    metadata={"approved_at": result.approved_at},
                )
        except ValueError as error:
            _handle(error)
        return Response(PurchaseInvoiceSerializer(result).data)


class PurchaseInvoiceMatchAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        require_purchase_permission(request, PermissionCode.PURCHASE_VIEW)
        try:
            result = _matching_use_case().execute(
                request.business.id, pk, persist=False,
            )
        except ValueError as error:
            _handle(error)
        return Response(PurchaseInvoiceMatchResponseSerializer(result).data)

    def post(self, request, pk):
        require_purchase_permission(request, PermissionCode.PURCHASE_INVOICE_MATCH)
        try:
            with transaction.atomic():
                repository = _repository()
                before = repository.get_by_id_for_business(pk, request.business.id)
                result = _matching_use_case().execute(
                    request.business.id, pk, persist=True,
                )
                invoice = repository.get_by_id_for_business(pk, request.business.id)
                _record_invoice_event(
                    invoice, request.user, PurchaseInvoiceEvent.EventType.MATCH_PERSISTED,
                    previous_status=invoice.status if invoice else None,
                    metadata={
                        "previous_matching_status": getattr(before.matching_status, "value", before.matching_status) if before else None,
                        "result": PurchaseInvoiceMatchResponseSerializer(result).data,
                    },
                )
        except ValueError as error:
            _handle(error)
        return Response(PurchaseInvoiceMatchResponseSerializer(result).data)


class PurchaseInvoicePostAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        require_purchase_permission(request, PermissionCode.PURCHASE_INVOICE_POST)
        serializer = PostPurchaseInvoiceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                before = _repository().get_by_id_for_business(pk, request.business.id)
                result = _posting_use_case().execute(
                    PostPurchaseInvoiceDTO(
                        business_id=request.business.id,
                        purchase_invoice_id=pk,
                        posted_by_id=request.user.id,
                        posted_at=timezone.now(),
                        due_date=serializer.validated_data["due_date"],
                    )
                )
                _record_invoice_event(
                    result.invoice, request.user, PurchaseInvoiceEvent.EventType.POSTED,
                    previous_status=before.status if before else None,
                    metadata={
                        "accounts_payable_id": result.accounts_payable.id,
                        "amount": result.accounts_payable.amount,
                        "due_date": result.accounts_payable.due_date,
                    },
                )
        except ValueError as error:
            _handle(error)
        return Response(
            PostPurchaseInvoiceResponseSerializer(result).data,
            status=status.HTTP_200_OK,
        )


class CancelPurchaseInvoiceRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(allow_blank=False, trim_whitespace=True)

    def to_internal_value(self, data):
        if isinstance(data, dict):
            unknown = set(data) - {"reason"}
            if unknown:
                raise serializers.ValidationError({
                    key: "Unknown fields are not allowed." for key in sorted(unknown)
                })
        return super().to_internal_value(data)


class PurchaseInvoiceCancelAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        require_purchase_permission(request, PermissionCode.PURCHASE_INVOICE_CANCEL)
        serializer = CancelPurchaseInvoiceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                before = _repository().get_by_id_for_business(pk, request.business.id)
                invoice = CancelPurchaseInvoice(
                    _repository(), DjangoAccountsPayableRepository(), _transaction_manager(),
                ).execute(CancelPurchaseInvoiceDTO(
                    business_id=request.business.id,
                    purchase_invoice_id=pk,
                    cancelled_by_id=request.user.id,
                    cancelled_at=timezone.now(),
                    reason=serializer.validated_data["reason"],
                ))
                _record_invoice_event(
                    invoice, request.user, PurchaseInvoiceEvent.EventType.CANCELLED,
                    previous_status=before.status if before else None,
                    metadata={"reason": invoice.cancellation_reason},
                )
        except ValueError as error:
            _handle(error)
        return Response(PurchaseInvoiceSerializer(invoice).data)
