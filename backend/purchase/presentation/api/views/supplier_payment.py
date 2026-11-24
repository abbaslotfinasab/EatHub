from datetime import date
from decimal import Decimal

from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.views import TenantAPIView
from core.enums import PermissionCode
from purchase.application.dto.supplier_payment import (
    CreateSupplierPaymentDTO,
    ListSupplierPaymentsQuery,
)
from purchase.application.dto.supplier_payment_allocation import (
    ListSupplierPaymentAllocationTotalsQuery,
)
from purchase.domain.enums.payment_method import PaymentMethod
from purchase.composition import (
    create_supplier_payment_use_case,
    get_supplier_payment_use_case,
    list_supplier_payment_allocation_totals_use_case,
    list_supplier_payments_use_case,
)
from purchase.presentation.api.serializers.supplier_payment import (
    CreateSupplierPaymentSerializer,
    SupplierPaymentSerializer,
)
from purchase.presentation.api.permissions import require_purchase_permission



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
        require_purchase_permission(request, PermissionCode.PURCHASE_VIEW)
        method = request.query_params.get("method")
        try:
            parsed_method = PaymentMethod(method) if method else None
        except ValueError as error:
            raise ValidationError({"method": "Invalid payment method."}) from error

        try:
            payments = list_supplier_payments_use_case().execute(
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

        payment_ids = [payment.id for payment in payments if payment.id is not None]
        allocated_by_payment = list_supplier_payment_allocation_totals_use_case().execute(
            ListSupplierPaymentAllocationTotalsQuery(
                business_id=request.business.id,
                supplier_payment_ids=payment_ids,
            )
        )

        data = SupplierPaymentSerializer(payments, many=True).data
        for payment, item in zip(payments, data):
            allocated = allocated_by_payment.get(payment.id, Decimal("0.00"))
            item["allocated_amount"] = str(allocated.quantize(Decimal("0.01")))
            item["remaining_amount"] = str(
                (payment.amount - allocated).quantize(Decimal("0.01"))
            )
        return Response(data)

    def post(self, request):
        require_purchase_permission(request, PermissionCode.PURCHASE_PAYMENT_CREATE)
        if "invoice_id" in request.data:
            raise ValidationError({
                "invoice_id": "Invoice allocation is not supported in this phase."
            })
        serializer = CreateSupplierPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            payment_result = create_supplier_payment_use_case().execute(
                CreateSupplierPaymentDTO(
                    business_id=request.business.id,
                    supplier_id=data["supplier_id"],
                    amount=data["amount"],
                    payment_date=data["payment_date"],
                    method=PaymentMethod(data["method"]),
                    idempotency_key=data["idempotency_key"],
                )
            )
            payment, replayed = payment_result
        except ValueError as error:
            _handle_payment_error(error)
        return Response(
            SupplierPaymentSerializer(payment).data,
            status=(status.HTTP_200_OK if replayed else status.HTTP_201_CREATED),
        )


class SupplierPaymentDetailAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        require_purchase_permission(request, PermissionCode.PURCHASE_VIEW)
        try:
            payment = get_supplier_payment_use_case().execute(
                pk,
                request.business.id,
            )
        except ValueError as error:
            _handle_payment_error(error)
        return Response(SupplierPaymentSerializer(payment).data)
