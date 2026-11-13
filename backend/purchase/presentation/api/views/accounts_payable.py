from datetime import date

from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.views import TenantAPIView
from core.enums import PermissionCode
from purchase.application.dto.accounts_payable import ListAccountsPayablesQuery
from purchase.application.dto.accounts_payable_payment_eligibility import (
    GetAccountsPayablePaymentEligibilityQuery,
)
from purchase.application.use_cases.accounts_payable.get_accounts_payable_payment_eligibility import (
    GetAccountsPayablePaymentEligibility,
)
from purchase.application.use_cases.accounts_payable.get_accounts_payable import (
    GetAccountsPayableUseCase,
)
from purchase.application.use_cases.accounts_payable.list_accounts_payables import (
    ListAccountsPayablesUseCase,
)
from purchase.domain.enums.accounts_payable_status import AccountsPayableStatus
from purchase.infrastructure.persistence.django.repositories.accounts_payable_repository import (
    DjangoAccountsPayableRepository,
)
from purchase.infrastructure.persistence.django.repositories.payment_allocation_repository import (
    DjangoPaymentAllocationRepository,
)
from purchase.presentation.api.serializers.accounts_payable import (
    AccountsPayableListSerializer,
    AccountsPayableSerializer,
)
from purchase.presentation.api.serializers.accounts_payable_payment_eligibility import (
    AccountsPayablePaymentEligibilitySerializer,
)
from purchase.presentation.api.permissions import require_purchase_permission


def _repository() -> DjangoAccountsPayableRepository:
    return DjangoAccountsPayableRepository()


def _handle(error: ValueError) -> None:
    detail = str(error)
    if "does not exist" in detail:
        raise NotFound({"detail": detail})
    raise ValidationError({"detail": detail})


def _optional_id(value: str | None, name: str) -> int | None:
    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as error:
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


class AccountsPayableListAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        require_purchase_permission(request, PermissionCode.PURCHASE_VIEW)
        raw_status = request.query_params.get("status")
        try:
            payable_status = AccountsPayableStatus(raw_status) if raw_status else None
        except ValueError as error:
            raise ValidationError({"status": "Invalid accounts payable status."}) from error
        try:
            payables = ListAccountsPayablesUseCase(_repository()).execute(
                ListAccountsPayablesQuery(
                    business_id=request.business.id,
                    status=payable_status,
                    supplier_id=_optional_id(request.query_params.get("supplier_id"), "supplier_id"),
                    due_date_from=_optional_date(request.query_params.get("due_date_from"), "due_date_from"),
                    due_date_to=_optional_date(request.query_params.get("due_date_to"), "due_date_to"),
                ),
            )
        except ValueError as error:
            _handle(error)
        return Response(AccountsPayableListSerializer(payables, many=True).data)


class AccountsPayableDetailAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        require_purchase_permission(request, PermissionCode.PURCHASE_VIEW)
        try:
            payable = GetAccountsPayableUseCase(_repository()).execute(
                pk,
                request.business.id,
            )
        except ValueError as error:
            _handle(error)
        return Response(AccountsPayableSerializer(payable).data)


class AccountsPayablePaymentEligibilityAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        require_purchase_permission(request, PermissionCode.PURCHASE_VIEW)
        try:
            result = GetAccountsPayablePaymentEligibility(
                _repository(),
                DjangoPaymentAllocationRepository(),
            ).execute(
                GetAccountsPayablePaymentEligibilityQuery(
                    business_id=request.business.id,
                    accounts_payable_id=pk,
                ),
            )
        except ValueError as error:
            _handle(error)
        return Response(AccountsPayablePaymentEligibilitySerializer(result).data)
