from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.views import TenantAPIView
from purchase.application.dto.goods_receipt import (
    CreateGoodsReceiptDTO,
    CreateGoodsReceiptItemDTO,
    ListGoodsReceiptsQuery,
)
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
from purchase.infrastructure.persistence.django.repositories.purchase_order_line_reader import (
    DjangoPurchaseOrderLineReader,
)
from purchase.infrastructure.persistence.django.repositories.purchase_order_repository import (
    DjangoPurchaseOrderRepository,
)
from purchase.infrastructure.persistence.transaction import (
    DjangoTransactionManager,
)
from purchase.infrastructure.services.stock_transaction_gateway import (
    DjangoStockTransactionGateway,
)
from purchase.presentation.api.serializers.goods_receipt import (
    CreateGoodsReceiptSerializer,
    GoodsReceiptSerializer,
)


def _goods_receipt_repository() -> DjangoGoodsReceiptRepository:
    return DjangoGoodsReceiptRepository()


def _create_goods_receipt_use_case() -> CreateGoodsReceiptUseCase:
    return CreateGoodsReceiptUseCase(
        _goods_receipt_repository(),
        DjangoPurchaseOrderRepository(),
        DjangoPurchaseOrderLineReader(),
        DjangoStockTransactionGateway(),
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
        )
        for item in items
    ]


class GoodsReceiptListCreateAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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
        serializer = CreateGoodsReceiptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            receipt = _create_goods_receipt_use_case().execute(
                CreateGoodsReceiptDTO(
                    business_id=request.business.id,
                    purchase_order_id=data["purchase_order_id"],
                    received_by_id=request.user.id,
                    received_date=data["received_date"],
                    notes=data.get("notes", ""),
                    items=_item_dtos(data["items"]),
                )
            )
        except ValueError as error:
            _handle_goods_receipt_error(error)

        return Response(
            GoodsReceiptSerializer(receipt).data,
            status=status.HTTP_201_CREATED,
        )


class GoodsReceiptDetailAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
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
