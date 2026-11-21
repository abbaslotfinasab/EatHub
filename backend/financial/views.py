from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.views import ExplicitTenantAPIView
from core.enums import PermissionCode
from financial.infrastructure.django.customer_account_read_repository import (
    DjangoCustomerAccountReadRepository,
)
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
        account = DjangoCustomerAccountReadRepository().get_account_for_business(
            request.business.id, customer_id
        )
        if account is None:
            raise NotFound()
        return Response(CustomerAccountSerializer(account).data)


class CustomerCreditAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, customer_id):
        _require_financial_access(
            request, "You do not have permission to change customer balances."
        )
        serializer = CustomerBalanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = DjangoCustomerAccountReadRepository().get_customer_for_business(
            request.business.id, customer_id
        )
        if customer is None:
            raise NotFound()
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
        repository = DjangoCustomerAccountReadRepository()
        account = repository.get_account_for_business(
            request.business.id, customer_id
        )
        if account is None:
            raise NotFound()
        transactions = repository.list_transactions_for_account(account)
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
        customer = DjangoCustomerAccountReadRepository().get_customer_for_business(
            request.business.id, customer_id
        )
        if customer is None:
            raise NotFound()
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
        customer = DjangoCustomerAccountReadRepository().get_customer_for_business(
            request.business.id, customer_id
        )
        if customer is None:
            raise NotFound()
        WalletService.adjust(
            business=request.business,
            customer=customer,
            amount=serializer.validated_data["amount"],
            description=serializer.validated_data.get("description", ""),
        )
        return Response({"status": "adjusted"})
