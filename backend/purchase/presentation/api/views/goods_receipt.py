from rest_framework import serializers, status
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.views import TenantAPIView
from core.enums import PermissionCode
from inventory.application.use_cases.receive_stock import ReceiveStockUseCase
from inventory.infrastructure.django.models import InventoryV1StockMovement
from inventory.infrastructure.django.repositories import (
    DjangoIngredientRepository,
    DjangoStockMovementRepository,
    DjangoStockRepository,
    DjangoWarehouseRepository,
)
from inventory.infrastructure.django.unit_of_work import DjangoInventoryUnitOfWork
from purchase.application.dto.goods_receipt import (
    CreateGoodsReceiptDTO,
    CreateGoodsReceiptItemDTO,
    ListGoodsReceiptsQuery,
)
from purchase.application.exceptions import GoodsReceiptIdempotencyPayloadMismatch
from purchase.domain.enums.purchase_unit import PurchaseUnit
from purchase.application.use_cases.goods_receipt.create_goods_receipt import (
    CreateGoodsReceiptUseCase,
)
from purchase.application.use_cases.goods_receipt.get_goods_receipt import (
    GetGoodsReceiptUseCase,
)
from purchase.application.use_cases.goods_receipt.list_goods_receipts import (
    ListGoodsReceiptsUseCase,
)
from purchase.infrastructure.persistence.django.repositories.goods_receipt_repository import (
    DjangoGoodsReceiptRepository,
)
from purchase.models import GoodsReceiptInventoryMovementLink
from purchase.infrastructure.persistence.django.repositories.purchase_order_line_reader import (
    DjangoPurchaseOrderLineReader,
)
from purchase.infrastructure.persistence.django.repositories.purchase_order_repository import (
    DjangoPurchaseOrderRepository,
)
from purchase.infrastructure.persistence.transaction import (
    DjangoTransactionManager,
)
from purchase.infrastructure.services.inventory_receipt_gateway import (
    DjangoInventoryReceiptGateway,
)
from purchase.presentation.api.permissions import require_purchase_permission
from purchase.presentation.api.serializers.goods_receipt import (
    CreateGoodsReceiptSerializer,
    GoodsReceiptSerializer,
)


class GoodsReceiptIdempotencyConflictAPIException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = {
        "code": "idempotency_key_reused",
        "detail": "This idempotency key was already used with different receipt data.",
    }
    default_code = "idempotency_key_reused"


def _goods_receipt_repository() -> DjangoGoodsReceiptRepository:
    return DjangoGoodsReceiptRepository()


def _create_goods_receipt_use_case() -> CreateGoodsReceiptUseCase:
    inventory_use_case = ReceiveStockUseCase(
        DjangoWarehouseRepository(),
        DjangoIngredientRepository(),
        DjangoStockRepository(),
        DjangoStockMovementRepository(),
        DjangoInventoryUnitOfWork(),
    )
    return CreateGoodsReceiptUseCase(
        _goods_receipt_repository(),
        DjangoPurchaseOrderRepository(),
        DjangoPurchaseOrderLineReader(),
        DjangoInventoryReceiptGateway(inventory_use_case),
        DjangoTransactionManager(),
    )


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


def _parse_optional_datetime(
    value: str | None,
    field_name: str,
):
    if value is None or value == "":
        return None

    try:
        return serializers.DateTimeField().to_internal_value(value)
    except ValidationError as error:
        raise ValidationError({field_name: error.detail}) from error


def _handle_goods_receipt_error(error: ValueError) -> None:
    detail = str(error)

    if "does not exist" in detail:
        raise NotFound({"detail": detail})

    raise ValidationError({"detail": detail})


def _item_dtos(items: list[dict]) -> list[CreateGoodsReceiptItemDTO]:
    return [
        CreateGoodsReceiptItemDTO(
            purchase_order_item_id=item["purchase_order_item_id"],
            received_quantity=item["received_quantity"],
            rejected_quantity=item.get("rejected_quantity", 0),
            purchase_unit=PurchaseUnit(item["purchase_unit"]),
        )
        for item in items
    ]


class GoodsReceiptListCreateAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        require_purchase_permission(request, PermissionCode.PURCHASE_VIEW)
        try:
            receipts = ListGoodsReceiptsUseCase(
                _goods_receipt_repository()
            ).execute(
                ListGoodsReceiptsQuery(
                    business_id=request.business.id,
                    purchase_order_id=_parse_optional_id(
                        request.query_params.get("purchase_order_id"),
                        "purchase_order_id",
                    ),
                    received_by_id=_parse_optional_id(
                        request.query_params.get("received_by_id"),
                        "received_by_id",
                    ),
                    received_from=_parse_optional_datetime(
                        request.query_params.get("received_from"),
                        "received_from",
                    ),
                    received_to=_parse_optional_datetime(
                        request.query_params.get("received_to"),
                        "received_to",
                    ),
                )
            )
        except ValueError as error:
            _handle_goods_receipt_error(error)

        return Response(GoodsReceiptSerializer(receipts, many=True).data)

    def post(self, request):
        require_purchase_permission(request, PermissionCode.PURCHASE_RECEIPT_CREATE)
        serializer = CreateGoodsReceiptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            result = _create_goods_receipt_use_case().execute(
                CreateGoodsReceiptDTO(
                    business_id=request.business.id,
                    purchase_order_id=data["purchase_order_id"],
                    received_by_id=request.user.id,
                    received_date=data["received_date"],
                    notes=data.get("notes", ""),
                    warehouse_id=data.get("warehouse_id"),
                    items=_item_dtos(data["items"]),
                    idempotency_key=data["idempotency_key"],
                )
            )
        except GoodsReceiptIdempotencyPayloadMismatch as error:
            raise GoodsReceiptIdempotencyConflictAPIException() from error
        except ValueError as error:
            _handle_goods_receipt_error(error)

        return Response(
            GoodsReceiptSerializer(result.receipt).data,
            status=(
                status.HTTP_200_OK
                if result.replayed
                else status.HTTP_201_CREATED
            ),
        )


class GoodsReceiptDetailAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        require_purchase_permission(request, PermissionCode.PURCHASE_VIEW)
        try:
            receipt = GetGoodsReceiptUseCase(
                _goods_receipt_repository()
            ).execute(
                goods_receipt_id=pk,
                business_id=request.business.id,
            )
        except ValueError as error:
            _handle_goods_receipt_error(error)

        return Response(GoodsReceiptSerializer(receipt).data)


class GoodsReceiptTraceUnavailableAPIException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = {
        "code": "goods_receipt_trace_unavailable",
        "detail": "This historical receipt movement has no verified receipt-line link.",
    }
    default_code = "goods_receipt_trace_unavailable"


class GoodsReceiptStockMovementTraceAPIView(TenantAPIView):
    """Resolve a receipt movement through its protected link to its supplier."""

    permission_classes = [IsAuthenticated]

    def get(self, request, movement_id):
        require_purchase_permission(request, PermissionCode.PURCHASE_VIEW)

        movement = InventoryV1StockMovement.objects.filter(
            pk=movement_id,
            business_id=request.business.id,
        ).select_related(
            "stock__warehouse",
            "stock__ingredient",
        ).first()
        if movement is None:
            raise NotFound({"detail": "Stock movement does not exist in this business."})
        if movement.source_type != "goods_receipt" or movement.movement_type != "receipt":
            raise ValidationError(
                {"detail": "The requested StockMovement is not a goods receipt movement."}
            )

        link = GoodsReceiptInventoryMovementLink.objects.select_related(
            "receipt_item__receipt__purchase_order__supplier",
            "receipt_item__purchase_order_item__ingredient",
        ).filter(
            movement_id=movement.pk,
            receipt_item__receipt__business_id=request.business.id,
        ).first()
        if link is None:
            raise GoodsReceiptTraceUnavailableAPIException()

        receipt_item = link.receipt_item
        receipt = receipt_item.receipt
        purchase_order = receipt.purchase_order
        purchase_order_item = receipt_item.purchase_order_item
        supplier = purchase_order.supplier

        if (
            movement.source_document_id != receipt.pk
            or movement.source_line_id != receipt_item.pk
            or movement.stock.business_id != request.business.id
            or movement.stock.warehouse.business_id != request.business.id
            or movement.stock.ingredient.business_id != request.business.id
            or receipt.business_id != request.business.id
            or purchase_order.business_id != request.business.id
            or supplier.business_id != request.business.id
            or purchase_order_item.purchase_order_id != purchase_order.pk
            or purchase_order_item.ingredient_id != movement.stock.ingredient_id
        ):
            raise GoodsReceiptTraceUnavailableAPIException(
                "The linked receipt, purchase order, supplier, and stock references are inconsistent."
            )

        return Response({
            "movement": {
                "id": movement.pk,
                "business_id": movement.business_id,
                "source_type": movement.source_type,
                "source_document_id": movement.source_document_id,
                "source_line_id": movement.source_line_id,
                "operation_kind": movement.operation_kind,
                "movement_type": movement.movement_type,
                "direction": movement.direction,
                "quantity": movement.quantity,
                "unit": movement.unit,
                "unit_cost": movement.unit_cost,
                "occurred_at": movement.occurred_at,
                "actor_id": movement.actor_id,
                "stock_id": movement.stock_id,
                "warehouse_id": movement.stock.warehouse_id,
                "warehouse_name": movement.stock.warehouse.name,
                "ingredient_id": movement.stock.ingredient_id,
                "ingredient_name": movement.stock.ingredient.name,
            },
            "goods_receipt": {
                "id": receipt.pk,
                "business_id": receipt.business_id,
                "received_date": receipt.received_date,
                "received_by_id": receipt.received_by_id,
                "purchase_order_id": receipt.purchase_order_id,
            },
            "goods_receipt_item": {
                "id": receipt_item.pk,
                "purchase_order_item_id": receipt_item.purchase_order_item_id,
                "received_quantity": receipt_item.received_quantity,
                "rejected_quantity": receipt_item.rejected_quantity,
                "purchase_unit": receipt_item.purchase_unit,
            },
            "purchase_order": {
                "id": purchase_order.pk,
                "status": purchase_order.status,
                "supplier_id": supplier.pk,
                "supplier_name": supplier.name,
            },
            "purchase_order_item": {
                "id": purchase_order_item.pk,
                "ingredient_id": purchase_order_item.ingredient_id,
                "ordered_quantity": purchase_order_item.quantity,
                "purchase_unit": purchase_order_item.purchase_unit,
                "unit_price": purchase_order_item.unit_price,
            },
            "supplier": {
                "id": supplier.pk,
                "name": supplier.name,
            },
        })


