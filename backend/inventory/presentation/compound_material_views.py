from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.views import TenantAPIView
from core.enums import PermissionCode
from inventory.application.exceptions import MasterDataConflict
from inventory.infrastructure.django.compound_material_repository import DjangoCompoundMaterialRepository
from inventory.presentation.serializers.compound_material import (
    CompoundMaterialCreateSerializer,
    CompoundMaterialListQuerySerializer,
    CompoundMaterialPageSerializer,
    CompoundMaterialSerializer,
    CompoundMaterialUpdateSerializer,
)


def _require_permission(request, permission: PermissionCode) -> None:
    if permission.value not in request.permissions:
        raise PermissionDenied("You do not have permission to manage Compound Materials.")


def _save_or_validate(call):
    try:
        return call()
    except MasterDataConflict as error:
        raise ValidationError({error.field: str(error)}) from error


class CompoundMaterialListCreateAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_permission(request, PermissionCode.INVENTORY_VIEW)
        serializer = CompoundMaterialListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data
        page = DjangoCompoundMaterialRepository.list_for_business(
            request.business.id,
            page=params["page"],
            page_size=params["page_size"],
            search=params.get("search"),
            is_active=params.get("is_active"),
        )
        return Response(CompoundMaterialPageSerializer(page).data)

    def post(self, request):
        _require_permission(request, PermissionCode.INVENTORY_COMPOUND_MANAGE)
        serializer = CompoundMaterialCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        material = _save_or_validate(lambda: DjangoCompoundMaterialRepository().create(
            request.business.id, serializer.validated_data,
        ))
        return Response(CompoundMaterialSerializer(material).data, status=status.HTTP_201_CREATED)


class CompoundMaterialDetailAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        _require_permission(request, PermissionCode.INVENTORY_VIEW)
        material = DjangoCompoundMaterialRepository.get_for_business(request.business.id, pk)
        if material is None:
            raise NotFound("Compound material does not exist in this business.")
        return Response(CompoundMaterialSerializer(material).data)

    def patch(self, request, pk):
        _require_permission(request, PermissionCode.INVENTORY_COMPOUND_MANAGE)
        serializer = CompoundMaterialUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        material = _save_or_validate(lambda: DjangoCompoundMaterialRepository().update(
            request.business.id, pk, serializer.validated_data,
        ))
        if material is None:
            raise NotFound("Compound material does not exist in this business.")
        return Response(CompoundMaterialSerializer(material).data)
