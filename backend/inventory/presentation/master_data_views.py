from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.views import TenantAPIView
from core.enums import PermissionCode
from inventory.application.exceptions import MasterDataConflict
from inventory.infrastructure.django.master_data_repository import DjangoMasterDataRepository
from inventory.presentation.serializers.master_data import (
    ItemCreateSerializer,
    ItemQuerySerializer,
    ItemSerializer,
    ItemUpdateSerializer,
    WarehouseCreateSerializer,
    WarehouseQuerySerializer,
    WarehouseSerializer,
    WarehouseUpdateSerializer,
)


def _require_permission(request, permission: PermissionCode) -> None:
    if permission.value not in request.permissions:
        raise PermissionDenied("You do not have permission to manage Inventory master data.")


def _save_or_validate(call):
    try:
        return call()
    except MasterDataConflict as error:
        raise ValidationError({error.field: str(error)}) from error


class ItemListCreateAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_permission(request, PermissionCode.INVENTORY_VIEW)
        query = ItemQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        count, results = DjangoMasterDataRepository.list_items(
            request.business.id,
            page=params["page"],
            page_size=params["page_size"],
            search=params.get("search"),
            is_active=params.get("is_active"),
            unit=params.get("unit"),
            preparation_level=params.get("preparation_level"),
        )
        return Response({
            "count": count,
            "page": params["page"],
            "page_size": params["page_size"],
            "results": ItemSerializer(results, many=True).data,
        })

    def post(self, request):
        _require_permission(request, PermissionCode.INVENTORY_ITEM_MANAGE)
        serializer = ItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = _save_or_validate(
            lambda: DjangoMasterDataRepository().save_item(
                request.business.id, None, serializer.validated_data
            )
        )
        return Response(ItemSerializer(item).data, status=status.HTTP_201_CREATED)


class ItemDetailAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        _require_permission(request, PermissionCode.INVENTORY_VIEW)
        item = DjangoMasterDataRepository.get_item(request.business.id, pk)
        if item is None:
            raise NotFound("Item does not exist in this business.")
        return Response(ItemSerializer(item).data)

    def patch(self, request, pk):
        _require_permission(request, PermissionCode.INVENTORY_ITEM_MANAGE)
        serializer = ItemUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        item = _save_or_validate(
            lambda: DjangoMasterDataRepository().save_item(
                request.business.id, pk, serializer.validated_data
            )
        )
        if item is None:
            raise NotFound("Item does not exist in this business.")
        return Response(ItemSerializer(item).data)


class WarehouseListCreateAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_permission(request, PermissionCode.INVENTORY_VIEW)
        query = WarehouseQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        count, results = DjangoMasterDataRepository.list_warehouses(
            request.business.id,
            page=params["page"],
            page_size=params["page_size"],
            search=params.get("search"),
            is_active=params.get("is_active"),
            is_default=params.get("is_default"),
        )
        return Response({
            "count": count,
            "page": params["page"],
            "page_size": params["page_size"],
            "results": WarehouseSerializer(results, many=True).data,
        })

    def post(self, request):
        _require_permission(request, PermissionCode.INVENTORY_WAREHOUSE_MANAGE)
        serializer = WarehouseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        warehouse = _save_or_validate(
            lambda: DjangoMasterDataRepository().save_warehouse(
                request.business.id, None, serializer.validated_data
            )
        )
        return Response(WarehouseSerializer(warehouse).data, status=status.HTTP_201_CREATED)


class WarehouseDetailAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        _require_permission(request, PermissionCode.INVENTORY_VIEW)
        warehouse = DjangoMasterDataRepository.get_warehouse(request.business.id, pk)
        if warehouse is None:
            raise NotFound("Warehouse does not exist in this business.")
        return Response(WarehouseSerializer(warehouse).data)

    def patch(self, request, pk):
        _require_permission(request, PermissionCode.INVENTORY_WAREHOUSE_MANAGE)
        current = DjangoMasterDataRepository.get_warehouse(request.business.id, pk)
        if current is None:
            raise NotFound("Warehouse does not exist in this business.")
        serializer = WarehouseUpdateSerializer(
            data=request.data, partial=True, instance=current
        )
        serializer.is_valid(raise_exception=True)
        warehouse = _save_or_validate(
            lambda: DjangoMasterDataRepository().save_warehouse(
                request.business.id, pk, serializer.validated_data
            )
        )
        if warehouse is None:
            raise NotFound("Warehouse does not exist in this business.")
        return Response(WarehouseSerializer(warehouse).data)
