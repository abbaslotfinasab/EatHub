from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.views import TenantAPIView
from purchase.application.dto.accounts_payable import ListAccountsPayablesQuery
from purchase.application.use_cases.accounts_payable.get_accounts_payable import (
    GetAccountsPayableUseCase,
)
from purchase.application.use_cases.accounts_payable.list_accounts_payables import (
    ListAccountsPayablesUseCase,
)
from purchase.infrastructure.persistence.django.repositories.accounts_payable_repository import (
    DjangoAccountsPayableRepository,
)
from purchase.presentation.api.serializers.accounts_payable import AccountsPayableSerializer


def _repository() -> DjangoAccountsPayableRepository:
    return DjangoAccountsPayableRepository()


def _handle(error: ValueError) -> None:
    detail = str(error)
    if "does not exist" in detail:
        raise NotFound({"detail": detail})
    raise ValidationError({"detail": detail})


class AccountsPayableListAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            payables = ListAccountsPayablesUseCase(_repository()).execute(
                ListAccountsPayablesQuery(business_id=request.business.id),
            )
        except ValueError as error:
            _handle(error)
        return Response(AccountsPayableSerializer(payables, many=True).data)

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
