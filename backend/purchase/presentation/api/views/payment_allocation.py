from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from accounts.views import TenantAPIView
from purchase.application.dto.payment_allocation import (
    CreatePaymentAllocationCommand,
    ListPaymentAllocationsQuery,
)
from purchase.application.use_cases.payment_allocation.create_payment_allocation import (
    CreatePaymentAllocation,
)
from purchase.application.use_cases.payment_allocation.get_payment_allocation import (
    GetPaymentAllocation,
)
from purchase.application.use_cases.payment_allocation.list_payment_allocations import (
    ListPaymentAllocations,
)
from purchase.infrastructure.persistence.django.repositories.accounts_payable_repository import (
    DjangoAccountsPayableRepository,
)
from purchase.infrastructure.persistence.django.repositories.payment_allocation_repository import (
    DjangoPaymentAllocationRepository,
)
from purchase.infrastructure.persistence.django.repositories.supplier_payment_repository import (
    DjangoSupplierPaymentRepository,
)
from purchase.infrastructure.persistence.transaction import DjangoTransactionManager
from purchase.presentation.api.serializers.payment_allocation import (
    CreatePaymentAllocationSerializer,
    PaymentAllocationSerializer,
)


def _handle(error: ValueError) -> None:
    detail = str(error)
    if "does not exist" in detail:
        raise NotFound({"detail": detail})
    raise ValidationError({"detail": detail})


def _use_case() -> CreatePaymentAllocation:
    return CreatePaymentAllocation(
        DjangoAccountsPayableRepository(),
        DjangoSupplierPaymentRepository(),
        DjangoPaymentAllocationRepository(),
        DjangoTransactionManager(),
    )


class PaymentAllocationListCreateAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            allocations = ListPaymentAllocations(
                DjangoPaymentAllocationRepository(),
            ).execute(ListPaymentAllocationsQuery(
                business_id=request.business.id,
                accounts_payable_id=self._optional_id(request.query_params.get("accounts_payable_id")),
                supplier_payment_id=self._optional_id(request.query_params.get("supplier_payment_id")),
            ))
        except ValueError as error:
            _handle(error)
        return Response(PaymentAllocationSerializer(allocations, many=True).data)

    def post(self, request):
        serializer = CreatePaymentAllocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            result = _use_case().execute(CreatePaymentAllocationCommand(
                business_id=request.business.id,
                accounts_payable_id=data["accounts_payable_id"],
                supplier_payment_id=data["supplier_payment_id"],
                amount=data["amount"],
                allocated_at=timezone.now(),
            ))
        except ValueError as error:
            _handle(error)
        return Response(
            PaymentAllocationSerializer(result.allocation).data,
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def _optional_id(value):
        if value in (None, ""):
            return None
        try:
            result = int(value)
        except (TypeError, ValueError) as error:
            raise ValidationError("Must be a valid positive integer.") from error
        if result <= 0:
            raise ValidationError("Must be a valid positive integer.")
        return result


class PaymentAllocationDetailAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            allocation = GetPaymentAllocation(
                DjangoPaymentAllocationRepository(),
            ).execute(pk, request.business.id)
        except ValueError as error:
            _handle(error)
        return Response(PaymentAllocationSerializer(allocation).data)
