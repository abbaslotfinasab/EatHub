from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.views import TenantAPIView
from purchase.application.dto.supplier import (
    CreateSupplierDTO,
    ListSuppliersQuery,
    UpdateSupplierDTO,
)
from purchase.application.use_cases.supplier.create_supplier import (
    CreateSupplierUseCase,
)
from purchase.application.use_cases.supplier.get_supplier import (
    GetSupplierUseCase,
)
from purchase.application.use_cases.supplier.list_suppliers import (
    ListSuppliersUseCase,
)
from purchase.application.use_cases.supplier.update_supplier import (
    UpdateSupplierUseCase,
)
from purchase.infrastructure.persistence.django.repositories.supplier_repository import (
    DjangoSupplierRepository,
)
from purchase.presentation.api.serializers.supplier import (
    SupplierCreateSerializer,
    SupplierSerializer,
    SupplierUpdateSerializer,
)


def _supplier_repository() -> DjangoSupplierRepository:
    return DjangoSupplierRepository()


def _parse_is_active(value: str | None) -> bool | None:
    if value is None or value == "":
        return None

    normalized = value.lower()

    if normalized in {"true", "1", "yes"}:
        return True

    if normalized in {"false", "0", "no"}:
        return False

    raise ValidationError({"is_active": "Must be a boolean value."})


def _handle_supplier_error(error: ValueError) -> None:
    detail = str(error)

    if "does not exist" in detail:
        raise NotFound({"detail": detail})

    raise ValidationError({"detail": detail})


class SupplierListCreateAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            suppliers = ListSuppliersUseCase(_supplier_repository()).execute(
                ListSuppliersQuery(
                    business_id=request.business.id,
                    is_active=_parse_is_active(
                        request.query_params.get("is_active")
                    ),
                    search=request.query_params.get("search"),
                )
            )
        except ValueError as error:
            _handle_supplier_error(error)

        return Response(
            SupplierSerializer(suppliers, many=True).data
        )

    def post(self, request):
        serializer = SupplierCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            supplier = CreateSupplierUseCase(_supplier_repository()).execute(
                CreateSupplierDTO(
                    business_id=request.business.id,
                    name=data["name"],
                    phone=data.get("phone", ""),
                    email=data.get("email", ""),
                    address=data.get("address", ""),
                    tax_number=data.get("tax_number", ""),
                    notes=data.get("notes", ""),
                )
            )
        except ValueError as error:
            _handle_supplier_error(error)

        return Response(
            SupplierSerializer(supplier).data,
            status=status.HTTP_201_CREATED,
        )


class SupplierDetailAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            supplier = GetSupplierUseCase(_supplier_repository()).execute(
                supplier_id=pk,
                business_id=request.business.id,
            )
        except ValueError as error:
            _handle_supplier_error(error)

        return Response(SupplierSerializer(supplier).data)

    def put(self, request, pk):
        serializer = SupplierUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            supplier = UpdateSupplierUseCase(_supplier_repository()).execute(
                UpdateSupplierDTO(
                    business_id=request.business.id,
                    supplier_id=pk,
                    name=data["name"],
                    phone=data.get("phone", ""),
                    email=data.get("email", ""),
                    address=data.get("address", ""),
                    tax_number=data.get("tax_number", ""),
                    notes=data.get("notes", ""),
                    is_active=data.get("is_active", True),
                )
            )
        except ValueError as error:
            _handle_supplier_error(error)

        return Response(SupplierSerializer(supplier).data)
