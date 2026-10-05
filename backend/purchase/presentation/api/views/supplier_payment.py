from datetime import date

from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.views import TenantAPIView
from purchase.application.dto.supplier_payment import (
    CreateSupplierPaymentDTO,
    ListSupplierPaymentsQuery,
)
from purchase.application.use_cases.supplier_payment.create_supplier_payment import (
    CreateSupplierPaymentUseCase,
)
from purchase.application.use_cases.supplier_payment.get_supplier_payment import (
    GetSupplierPaymentUseCase,
)
from purchase.application.use_cases.supplier_payment.list_supplier_payments import (
    ListSupplierPaymentsUseCase,
)
from purchase.domain.enums.payment_method import PaymentMethod
from purchase.infrastructure.persistence.django.repositories.supplier_payment_repository import (
    DjangoSupplierPaymentRepository,
)
from purchase.infrastructure.persistence.django.repositories.supplier_repository import (
    DjangoSupplierRepository,
)
from purchase.presentation.api.serializers.supplier_payment import (
    CreateSupplierPaymentSerializer,
    SupplierPaymentSerializer,
)


def _payment_repository() -> DjangoSupplierPaymentRepository:
    return DjangoSupplierPaymentRepository()


def _handle_payment_error(error: ValueError) -> None:
    detail = str(error)
    if "does not exist" in detail:
        raise NotFound({"detail": detail})
    raise ValidationError({"detail": detail})


def _optional_id(value: str | None, name: str) -> int | None:
    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except ValueError as error:
        raise ValidationError({name: "Must be a valid integer."}) from error
    if parsed <= 0:
        raise ValidationError({name: "Must be a positive integer."})
    return parsed


def _optional_date(value: str | None, name: str) -> date | None:
    if value in (None, ""):
        return None
    try:
        return serializers.DateField().to_internal_value(value)
    except ValidationError as error:
        raise ValidationError({name: error.detail}) from error


class SupplierPaymentListCreateAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        method = request.query_params.get("method")
        try:
            parsed_method = PaymentMethod(method) if method else None
        except ValueError as error:
            raise ValidationError({"method": "Invalid payment method."}) from error

        try:
            payments = ListSupplierPaymentsUseCase(_payment_repository()).execute(
                ListSupplierPaymentsQuery(
                    business_id=request.business.id,
                    supplier_id=_optional_id(
                        request.query_params.get("supplier_id"),
                        "supplier_id",
                    ),
                    method=parsed_method,
                    payment_date_from=_optional_date(
                        request.query_params.get("payment_date_from"),
                        "payment_date_from",
                    ),
                    payment_date_to=_optional_date(
                        request.query_params.get("payment_date_to"),
                        "payment_date_to",
                    ),
                )
            )
        except ValueError as error:
            _handle_payment_error(error)
        return Response(SupplierPaymentSerializer(payments, many=True).data)

    def post(self, request):
        if "invoice_id" in request.data:
            raise ValidationError({
                "invoice_id": "Invoice allocation is not supported in this phase."
            })
        serializer = CreateSupplierPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            payment = CreateSupplierPaymentUseCase(
                _payment_repository(),
                DjangoSupplierRepository(),
            ).execute(
                CreateSupplierPaymentDTO(
                    business_id=request.business.id,
                    supplier_id=data["supplier_id"],
                    amount=data["amount"],
                    payment_date=data["payment_date"],
                    method=PaymentMethod(data["method"]),
                )
            )
        except ValueError as error:
            _handle_payment_error(error)
        return Response(
            SupplierPaymentSerializer(payment).data,
            status=status.HTTP_201_CREATED,
        )


class SupplierPaymentDetailAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            payment = GetSupplierPaymentUseCase(_payment_repository()).execute(
                pk,
                request.business.id,
            )
        except ValueError as error:
            _handle_payment_error(error)
        return Response(SupplierPaymentSerializer(payment).data)
