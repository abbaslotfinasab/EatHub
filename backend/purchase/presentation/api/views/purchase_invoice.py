from datetime import date

from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.views import TenantAPIView
from purchase.application.dto.purchase_invoice import (
    ApprovePurchaseInvoiceDTO,
    CreatePurchaseInvoiceDTO,
    CreatePurchaseInvoiceItemDTO,
    ListPurchaseInvoicesQuery,
    UpdatePurchaseInvoiceDTO,
)
from purchase.application.use_cases.purchase_invoice.approve_purchase_invoice import ApprovePurchaseInvoiceUseCase
from purchase.application.use_cases.purchase_invoice.create_purchase_invoice import CreatePurchaseInvoiceUseCase
from purchase.application.use_cases.purchase_invoice.get_purchase_invoice import GetPurchaseInvoiceUseCase
from purchase.application.use_cases.purchase_invoice.list_purchase_invoices import ListPurchaseInvoicesUseCase
from purchase.application.use_cases.purchase_invoice.match_purchase_invoice import MatchPurchaseInvoiceUseCase
from purchase.application.use_cases.purchase_invoice.update_purchase_invoice import UpdatePurchaseInvoiceUseCase
from purchase.infrastructure.persistence.transaction import DjangoTransactionManager
from purchase.infrastructure.persistence.django.repositories.purchase_invoice_repository import DjangoPurchaseInvoiceRepository
from purchase.infrastructure.persistence.django.repositories.purchase_invoice_matching_repository import DjangoPurchaseInvoiceMatchingRepository
from purchase.presentation.api.serializers.purchase_invoice import (
    CreatePurchaseInvoiceSerializer,
    PurchaseInvoiceSerializer,
    PurchaseInvoiceMatchResponseSerializer,
    UpdatePurchaseInvoiceSerializer,
)


def _repository() -> DjangoPurchaseInvoiceRepository:
    return DjangoPurchaseInvoiceRepository()


def _transaction_manager() -> DjangoTransactionManager:
    return DjangoTransactionManager()


def _matching_use_case() -> MatchPurchaseInvoiceUseCase:
    return MatchPurchaseInvoiceUseCase(
        DjangoPurchaseInvoiceMatchingRepository(),
        _transaction_manager(),
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


class PurchaseInvoiceListCreateAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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
        serializer = CreatePurchaseInvoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
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
        except ValueError as error:
            _handle(error)
        return Response(PurchaseInvoiceSerializer(result).data, status=status.HTTP_201_CREATED)


class PurchaseInvoiceDetailAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            result = GetPurchaseInvoiceUseCase(_repository()).execute(pk, request.business.id)
        except ValueError as error:
            _handle(error)
        return Response(PurchaseInvoiceSerializer(result).data)

    def put(self, request, pk):
        serializer = UpdatePurchaseInvoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            result = UpdatePurchaseInvoiceUseCase(_repository()).execute(
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
        except ValueError as error:
            _handle(error)
        return Response(PurchaseInvoiceSerializer(result).data)


class PurchaseInvoiceApproveAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            result = ApprovePurchaseInvoiceUseCase(
                _repository(),
                _transaction_manager(),
            ).execute(
                ApprovePurchaseInvoiceDTO(
                    business_id=request.business.id,
                    purchase_invoice_id=pk,
                    approved_by_id=request.user.id,
                    approved_at=timezone.now(),
                )
            )
        except ValueError as error:
            _handle(error)
        return Response(PurchaseInvoiceSerializer(result).data)


class PurchaseInvoiceMatchAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            result = _matching_use_case().execute(
                request.business.id, pk, persist=False,
            )
        except ValueError as error:
            _handle(error)
        return Response(PurchaseInvoiceMatchResponseSerializer(result).data)

    def post(self, request, pk):
        try:
            result = _matching_use_case().execute(
                request.business.id, pk, persist=True,
            )
        except ValueError as error:
            _handle(error)
        return Response(PurchaseInvoiceMatchResponseSerializer(result).data)
