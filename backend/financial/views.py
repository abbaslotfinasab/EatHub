from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.views import ExplicitTenantAPIView
from core.enums import PermissionCode
from customer.models import Customer
from financial.models import CustomerAccount
from financial.serializers import (
    CustomerAccountSerializer,
    CustomerBalanceSerializer,
    CustomerTransactionSerializer,
)
from financial.services.wallet_service import WalletService


FINANCIAL_ROLE_CODES = {"OWNER", "MANAGER", "ACCOUNTANT"}


def _require_financial_access(request, message):
    role = getattr(request, "role", None)
    if (
        role is None
        or role.code not in FINANCIAL_ROLE_CODES
        or PermissionCode.PAYMENTS_MANAGE not in request.permissions
    ):
        raise PermissionDenied(message)


class CustomerAccountDetailAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, customer_id):
        account = get_object_or_404(
            CustomerAccount.objects.select_related("customer"),
            customer_id=customer_id,
            business=request.business,
        )
        return Response(CustomerAccountSerializer(account).data)


class CustomerCreditAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, customer_id):
        _require_financial_access(
            request, "You do not have permission to change customer balances."
        )
        serializer = CustomerBalanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = get_object_or_404(
            Customer,
            pk=customer_id,
            business=request.business,
        )
        WalletService.credit(
            business=request.business,
            customer=customer,
            amount=serializer.validated_data["amount"],
            description=serializer.validated_data.get("description", ""),
        )
        return Response({"status": "credited"})


class CustomerTransactionListAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, customer_id):
        account = get_object_or_404(
            CustomerAccount.objects.select_related("customer"),
            customer_id=customer_id,
            business=request.business,
        )
        transactions = account.transactions.all().order_by("-id")
        return Response(
            CustomerTransactionSerializer(transactions, many=True).data
        )


class CustomerDebitAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, customer_id):
        _require_financial_access(
            request, "You do not have permission to change customer balances."
        )
        serializer = CustomerBalanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = get_object_or_404(
            Customer,
            pk=customer_id,
            business=request.business,
        )
        WalletService.debit(
            business=request.business,
            customer=customer,
            amount=serializer.validated_data["amount"],
            description=serializer.validated_data.get("description", ""),
        )
        return Response({"status": "debited"})


class CustomerAdjustAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, customer_id):
        _require_financial_access(
            request, "You do not have permission to change customer balances."
        )
        serializer = CustomerBalanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = get_object_or_404(
            Customer,
            pk=customer_id,
            business=request.business,
        )
        WalletService.adjust(
            business=request.business,
            customer=customer,
            amount=serializer.validated_data["amount"],
            description=serializer.validated_data.get("description", ""),
        )
        return Response({"status": "adjusted"})
