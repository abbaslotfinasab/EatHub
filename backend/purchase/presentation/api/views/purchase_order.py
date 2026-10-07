from datetime import date

from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.views import TenantAPIView
from purchase.application.dto.purchase_order import (
    CreatePurchaseOrderDTO,
    CreatePurchaseOrderItemDTO,
    ListPurchaseOrdersQuery,
    UpdatePurchaseOrderDTO,
)
from purchase.application.use_cases.purchase_order.cancel_purchase_order import (
    CancelPurchaseOrderUseCase,
)
from purchase.application.use_cases.purchase_order.create_purchase_order import (
    CreatePurchaseOrderUseCase,
)
from purchase.application.use_cases.purchase_order.get_purchase_order import (
    GetPurchaseOrderUseCase,
)
from purchase.application.use_cases.purchase_order.list_purchase_orders import (
    ListPurchaseOrdersUseCase,
)
from purchase.application.use_cases.purchase_order.send_purchase_order import (
    SendPurchaseOrderUseCase,
)
from purchase.application.use_cases.purchase_order.update_purchase_order import (
    UpdatePurchaseOrderUseCase,
)
from purchase.domain.enums.purchase_order_status import PurchaseOrderStatus
from purchase.infrastructure.persistence.django.repositories.purchase_order_repository import (
    DjangoPurchaseOrderRepository,
)
from purchase.infrastructure.persistence.django.repositories.requisition_repository import (
    DjangoRequisitionRepository,
)
from purchase.infrastructure.persistence.django.repositories.supplier_repository import (
    DjangoSupplierRepository,
)
from purchase.infrastructure.persistence.transaction import DjangoTransactionManager
from purchase.presentation.api.serializers.purchase_order import (
    PurchaseOrderCreateSerializer,
    PurchaseOrderSerializer,
    PurchaseOrderUpdateSerializer,
)


def _purchase_order_repository() -> DjangoPurchaseOrderRepository:
    return DjangoPurchaseOrderRepository()


def _supplier_repository() -> DjangoSupplierRepository:
    return DjangoSupplierRepository()


def _requisition_repository() -> DjangoRequisitionRepository:
    return DjangoRequisitionRepository()


def _transaction_manager() -> DjangoTransactionManager:
    return DjangoTransactionManager()


def _parse_status(value: str | None) -> PurchaseOrderStatus | None:
    if value is None or value == "":
        return None

    try:
        return PurchaseOrderStatus(value)
    except ValueError as error:
        raise ValidationError(
            {"status": "Must be a valid purchase order status."}
        ) from error


def _parse_optional_id(value: str | None, field_name: str) -> int | None:
    if value is None or value == "":
        return None

    try:
        parsed = int(value)
    except ValueError as error:
        raise ValidationError({field_name: "Must be a valid integer."}) from error

    if parsed <= 0:
        raise ValidationError({field_name: "Must be a positive integer."})

    return parsed


def _parse_optional_date(value: str | None, field_name: str) -> date | None:
    if value is None or value == "":
        return None

    serializer = PurchaseOrderCreateSerializer()
    try:
        return serializer.fields["order_date"].to_internal_value(value)
    except ValidationError as error:
        raise ValidationError({field_name: error.detail}) from error


def _handle_purchase_order_error(error: ValueError) -> None:
    detail = str(error)

    if "does not exist" in detail:
        raise NotFound({"detail": detail})

    raise ValidationError({"detail": detail})


def _item_dtos(items: list[dict]) -> list[CreatePurchaseOrderItemDTO]:
    return [
        CreatePurchaseOrderItemDTO(
            ingredient_id=item["ingredient_id"],
            quantity=item["quantity"],
            unit_price=item["unit_price"],
        )
        for item in items
    ]


class PurchaseOrderListCreateAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            orders = ListPurchaseOrdersUseCase(
                _purchase_order_repository()
            ).execute(
                ListPurchaseOrdersQuery(
                    business_id=request.business.id,
                    status=_parse_status(request.query_params.get("status")),
                    supplier_id=_parse_optional_id(
                        request.query_params.get("supplier_id"),
                        "supplier_id",
                    ),
                    requisition_id=_parse_optional_id(
                        request.query_params.get("requisition_id"),
                        "requisition_id",
                    ),
                    order_date_from=_parse_optional_date(
                        request.query_params.get("order_date_from"),
                        "order_date_from",
                    ),
                    order_date_to=_parse_optional_date(
                        request.query_params.get("order_date_to"),
                        "order_date_to",
                    ),
                )
            )
        except ValueError as error:
            _handle_purchase_order_error(error)

        return Response(PurchaseOrderSerializer(orders, many=True).data)

    def post(self, request):
        serializer = PurchaseOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            order = CreatePurchaseOrderUseCase(
                _purchase_order_repository(),
                _supplier_repository(),
                _requisition_repository(),
            ).execute(
                CreatePurchaseOrderDTO(
                    business_id=request.business.id,
                    supplier_id=data["supplier_id"],
                    requisition_id=data.get("requisition_id"),
                    order_date=data["order_date"],
                    expected_date=data.get("expected_date"),
                    discount=data.get("discount"),
                    tax=data.get("tax"),
                    items=_item_dtos(data["items"]),
                )
            )
        except ValueError as error:
            _handle_purchase_order_error(error)

        return Response(
            PurchaseOrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class PurchaseOrderDetailAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            order = GetPurchaseOrderUseCase(
                _purchase_order_repository()
            ).execute(
                purchase_order_id=pk,
                business_id=request.business.id,
            )
        except ValueError as error:
            _handle_purchase_order_error(error)

        return Response(PurchaseOrderSerializer(order).data)

    def put(self, request, pk):
        serializer = PurchaseOrderUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            order = UpdatePurchaseOrderUseCase(
                _purchase_order_repository(),
                _transaction_manager(),
            ).execute(
                UpdatePurchaseOrderDTO(
                    business_id=request.business.id,
                    purchase_order_id=pk,
                    items=_item_dtos(data["items"]),
                    discount=data.get("discount"),
                    tax=data.get("tax"),
                )
            )
        except ValueError as error:
            _handle_purchase_order_error(error)

        return Response(PurchaseOrderSerializer(order).data)


class PurchaseOrderSendAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return _transition_response(SendPurchaseOrderUseCase, request, pk)


class PurchaseOrderCancelAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return _transition_response(CancelPurchaseOrderUseCase, request, pk)


def _transition_response(use_case_type, request, purchase_order_id: int):
    try:
        order = use_case_type(
            _purchase_order_repository(),
            _transaction_manager(),
        ).execute(
            purchase_order_id=purchase_order_id,
            business_id=request.business.id,
        )
    except ValueError as error:
        _handle_purchase_order_error(error)

    return Response(PurchaseOrderSerializer(order).data)
