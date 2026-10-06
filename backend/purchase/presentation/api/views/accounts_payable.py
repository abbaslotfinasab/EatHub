from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.views import TenantAPIView
from purchase.application.dto.accounts_payable import (
    CreateAccountsPayableDTO,
    ListAccountsPayablesQuery,
)
from purchase.application.use_cases.accounts_payable.create_accounts_payable import (
    CreateAccountsPayableUseCase,
)
from purchase.application.use_cases.accounts_payable.get_accounts_payable import (
    GetAccountsPayableUseCase,
)
from purchase.application.use_cases.accounts_payable.list_accounts_payables import (
    ListAccountsPayablesUseCase,
)
from purchase.application.use_cases.purchase_invoice.match_purchase_invoice import (
    MatchPurchaseInvoiceUseCase,
)
from purchase.infrastructure.persistence.django.repositories.accounts_payable_repository import (
    DjangoAccountsPayableRepository,
)
from purchase.infrastructure.persistence.django.repositories.purchase_invoice_matching_repository import (
    DjangoPurchaseInvoiceMatchingRepository,
)
from purchase.infrastructure.persistence.django.repositories.purchase_invoice_repository import (
    DjangoPurchaseInvoiceRepository,
)
from purchase.infrastructure.persistence.django.repositories.supplier_repository import (
    DjangoSupplierRepository,
)
from purchase.infrastructure.persistence.transaction import DjangoTransactionManager
from purchase.presentation.api.serializers.accounts_payable import (
    AccountsPayableSerializer,
    CreateAccountsPayableSerializer,
)


def _repository() -> DjangoAccountsPayableRepository:
    return DjangoAccountsPayableRepository()


def _create_use_case() -> CreateAccountsPayableUseCase:
    transaction_manager = DjangoTransactionManager()
    return CreateAccountsPayableUseCase(
        _repository(),
        DjangoPurchaseInvoiceRepository(),
        DjangoSupplierRepository(),
        MatchPurchaseInvoiceUseCase(
            DjangoPurchaseInvoiceMatchingRepository(),
            transaction_manager,
        ),
        transaction_manager,
    )


def _handle(error: ValueError) -> None:
    detail = str(error)
    if "does not exist" in detail:
        raise NotFound({"detail": detail})
    raise ValidationError({"detail": detail})


class AccountsPayableListCreateAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            payables = ListAccountsPayablesUseCase(_repository()).execute(
                ListAccountsPayablesQuery(business_id=request.business.id),
            )
        except ValueError as error:
            _handle(error)
        return Response(AccountsPayableSerializer(payables, many=True).data)

    def post(self, request):
        serializer = CreateAccountsPayableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            payable = _create_use_case().execute(
                CreateAccountsPayableDTO(
                    business_id=request.business.id,
                    source_invoice_id=data["source_invoice_id"],
                    due_date=data["due_date"],
                )
            )
        except ValueError as error:
            _handle(error)
        return Response(
            AccountsPayableSerializer(payable).data,
            status=status.HTTP_201_CREATED,
        )


class AccountsPayableDetailAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            payable = GetAccountsPayableUseCase(_repository()).execute(
                pk,
                request.business.id,
            )
        except ValueError as error:
            _handle(error)
        return Response(AccountsPayableSerializer(payable).data)
