from rest_framework import serializers, status
from rest_framework.exceptions import APIException, MethodNotAllowed, NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.views import TenantAPIView
from core.enums import PermissionCode
from inventory.application.exceptions import OperationConflict, ResourceNotFound
from inventory.domain.exceptions import InventoryDomainError
from inventory.domain.enums.movement import MovementType
from inventory.domain.value_objects.unit import Unit
from inventory.infrastructure.django.models import InventoryOperation
from inventory.infrastructure.django import operations_service as operations


class StrictSerializer(serializers.Serializer):
    """Reject unsupported keys from the raw payload before DRF normalizes it."""

    def to_internal_value(self, data):
        if hasattr(data, "keys"):
            unknown = set(data.keys()) - set(self.fields.keys())
            if unknown:
                raise serializers.ValidationError(
                    {key: "Unknown field." for key in sorted(unknown)}
                )
        return super().to_internal_value(data)


def _permission(request, code):
    if code.value not in request.permissions:
        raise PermissionDenied("You do not have permission for this Inventory operation.")


class OperationLineInputSerializer(StrictSerializer):
    ingredient_id = serializers.IntegerField(min_value=1)
    material_type = serializers.ChoiceField(choices=("raw", "compound"), required=False)
    quantity = serializers.DecimalField(max_digits=36, decimal_places=12, min_value=0, required=False, default=0)
    unit = serializers.ChoiceField(choices=[unit.value for unit in Unit])
    counted_quantity = serializers.DecimalField(max_digits=36, decimal_places=12, min_value=0, required=False)
    counted_unit_cost = serializers.DecimalField(max_digits=70, decimal_places=48, min_value=0, required=False)

class OperationCreateSerializer(StrictSerializer):
    warehouse_id = serializers.IntegerField(min_value=1)
    destination_warehouse_id = serializers.IntegerField(min_value=1, required=False)
    reference = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    reason = serializers.CharField(required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    lines = OperationLineInputSerializer(many=True, allow_empty=False)

    def validate(self, values):
        if self.context.get("operation_type") == InventoryOperation.Type.TRANSFER and not values.get("destination_warehouse_id"):
            raise serializers.ValidationError({"destination_warehouse_id": "Destination warehouse is required."})
        if self.context.get("operation_type") != InventoryOperation.Type.TRANSFER and values.get("destination_warehouse_id"):
            raise serializers.ValidationError({"destination_warehouse_id": "Only transfers have a destination."})
        if self.context.get("operation_type") == InventoryOperation.Type.ISSUE and not values.get("reason", "").strip():
            raise serializers.ValidationError({"reason": "An issue reason is required."})
        if self.context.get("operation_type") != InventoryOperation.Type.STOCKTAKE:
            for index, line in enumerate(values["lines"]):
                if line["quantity"] <= 0:
                    raise serializers.ValidationError({"lines": {index: {"quantity": "Quantity must be positive."}}})
        return values


class OpeningStockLineSerializer(StrictSerializer):
    ingredient_id = serializers.IntegerField(min_value=1)
    material_type = serializers.ChoiceField(choices=("raw", "compound"), required=False)
    quantity = serializers.DecimalField(max_digits=36, decimal_places=12, min_value=0)
    unit = serializers.ChoiceField(choices=[unit.value for unit in Unit])
    # Cost is expressed per canonical unit of the selected ingredient.
    unit_cost = serializers.DecimalField(
        max_digits=70,
        decimal_places=48,
        min_value=0,
        help_text=(
            "Accounting-currency amount per canonical ingredient unit. The Inventory V1 model "
            "does not persist a currency code."
        ),
    )

    def validate(self, values):
        if values["quantity"] <= 0:
            raise serializers.ValidationError({"quantity": "Quantity must be positive."})
        return values


class OpeningStockCreateSerializer(StrictSerializer):
    warehouse_id = serializers.IntegerField(min_value=1)
    reference = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    reason = serializers.CharField(required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    lines = OpeningStockLineSerializer(many=True, allow_empty=False)

    def validate(self, values):
        seen = set()
        duplicates = set()
        for line in values["lines"]:
            ingredient_id = line["ingredient_id"]
            if ingredient_id in seen:
                duplicates.add(ingredient_id)
            seen.add(ingredient_id)
        if duplicates:
            raise serializers.ValidationError({"lines": f"Duplicate ingredient IDs: {sorted(duplicates)}."})
        return values


class StocktakeCountSerializer(StrictSerializer):
    class Line(StrictSerializer):
        id = serializers.IntegerField(min_value=1)
        counted_quantity = serializers.DecimalField(max_digits=36, decimal_places=12, min_value=0)
        counted_unit_cost = serializers.DecimalField(max_digits=70, decimal_places=48, min_value=0, required=False)

    lines = Line(many=True, allow_empty=False)


class OperationQuerySerializer(serializers.Serializer):
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, required=False, default=20)


class ConflictResponse(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The Inventory operation conflicts with its current state."


def _operation_data(document):
    lines = []
    for line in document.lines.select_related("ingredient").order_by("pk"):
        lines.append({
            "id": line.pk, "ingredient_id": line.ingredient_id,
            "ingredient_name": line.ingredient.name,
            "material_type": "compound" if line.ingredient.preparation_level == "semi_prepared" else "raw",
            "quantity": str(line.quantity), "unit": line.unit,
            "system_quantity": None if line.system_quantity is None else str(line.system_quantity),
            "counted_quantity": None if line.counted_quantity is None else str(line.counted_quantity),
            "counted_unit_cost": None if line.counted_unit_cost is None else str(line.counted_unit_cost),
            "counted_by_id": line.counted_by_id,
            "counted_at": line.counted_at,
            "variance": None if line.counted_quantity is None else str(line.counted_quantity - (line.system_quantity or 0)),
            "in_transit_quantity": str(line.quantity) if document.status == InventoryOperation.Status.IN_TRANSIT else "0",
        })
    return {
        "id": document.pk, "type": document.operation_type, "status": document.status,
        "warehouse_id": document.warehouse_id, "warehouse_name": document.warehouse.name,
        "destination_warehouse_id": document.destination_warehouse_id,
        "destination_warehouse_name": document.destination_warehouse.name if document.destination_warehouse_id else None,
        "reference": document.reference, "reason": document.reason, "notes": document.notes,
        "created_by_id": document.created_by_id, "completed_by_id": document.completed_by_id,
        "created_at": document.created_at, "completed_at": document.completed_at, "lines": lines,
    }


def _run(call):
    try:
        return call()
    except ResourceNotFound as error:
        raise NotFound(str(error)) from error
    except OperationConflict as error:
        raise ConflictResponse(str(error)) from error
    except (InventoryDomainError, operations.OperationInputError, ValueError) as error:
        raise serializers.ValidationError({"detail": str(error)}) from error


class OperationCollectionAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]
    operation_type = None

    def get(self, request):
        _permission(request, PermissionCode.INVENTORY_VIEW)
        query = OperationQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        count, documents = operations.list_operations(request.business.id, self.operation_type, **params)
        return Response({"count": count, "page": params["page"], "page_size": params["page_size"], "results": [_operation_data(row) for row in documents]})

    def post(self, request):
        _permission(request, PermissionCode.INVENTORY_ADJUST)
        serializer = OperationCreateSerializer(data=request.data, context={"operation_type": self.operation_type})
        serializer.is_valid(raise_exception=True)
        document = _run(lambda: operations.create_operation(
            business_id=request.business.id, actor_id=request.user.pk,
            operation_type=self.operation_type, **serializer.validated_data,
        ))
        return Response(_operation_data(document), status=status.HTTP_201_CREATED)


class IssueListCreateAPIView(OperationCollectionAPIView):
    operation_type = InventoryOperation.Type.ISSUE


class TransferListCreateAPIView(OperationCollectionAPIView):
    operation_type = InventoryOperation.Type.TRANSFER


class StocktakeListCreateAPIView(OperationCollectionAPIView):
    operation_type = InventoryOperation.Type.STOCKTAKE


class OperationDetailAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]
    operation_type = None

    def get(self, request, pk):
        _permission(request, PermissionCode.INVENTORY_VIEW)
        return Response(_operation_data(_run(lambda: operations.get_operation(request.business.id, self.operation_type, pk))))

    def post(self, request, pk, action=None):
        if action is None:
            raise MethodNotAllowed("POST")
        _permission(request, PermissionCode.INVENTORY_ADJUST)
        actions = {
            (InventoryOperation.Type.ISSUE, "post"): lambda: operations.post_issue(business_id=request.business.id, actor_id=request.user.pk, operation_id=pk),
            (InventoryOperation.Type.ISSUE, "reverse"): lambda: operations.reverse_issue(business_id=request.business.id, actor_id=request.user.pk, operation_id=pk),
            (InventoryOperation.Type.TRANSFER, "dispatch"): lambda: operations.dispatch_transfer(business_id=request.business.id, actor_id=request.user.pk, operation_id=pk),
            (InventoryOperation.Type.TRANSFER, "receive"): lambda: operations.receive_transfer(business_id=request.business.id, actor_id=request.user.pk, operation_id=pk),
            (InventoryOperation.Type.STOCKTAKE, "approve"): lambda: operations.approve_stocktake(business_id=request.business.id, actor_id=request.user.pk, operation_id=pk),
            (self.operation_type, "cancel"): lambda: operations.cancel_operation(business_id=request.business.id, operation_type=self.operation_type, operation_id=pk),
        }
        call = actions.get((self.operation_type, action))
        if call is None:
            raise serializers.ValidationError({"action": "Unsupported operation transition."})
        return Response(_operation_data(_run(call)))

    def patch(self, request, pk):
        if self.operation_type != InventoryOperation.Type.STOCKTAKE:
            raise MethodNotAllowed("PATCH")
        _permission(request, PermissionCode.INVENTORY_ADJUST)
        serializer = StocktakeCountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        counts = {}
        for entry in serializer.validated_data["lines"]:
            counts[entry["id"]] = entry
        document = _run(lambda: operations.update_stocktake_counts(business_id=request.business.id, actor_id=request.user.pk, operation_id=pk, counts=counts))
        return Response(_operation_data(document))


class IssueDetailAPIView(OperationDetailAPIView):
    operation_type = InventoryOperation.Type.ISSUE


class TransferDetailAPIView(OperationDetailAPIView):
    operation_type = InventoryOperation.Type.TRANSFER


class StocktakeDetailAPIView(OperationDetailAPIView):
    operation_type = InventoryOperation.Type.STOCKTAKE


class OpeningStockCreateAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        _permission(request, PermissionCode.INVENTORY_ADJUST)
        serializer = OpeningStockCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = _run(lambda: operations.create_opening_stock(
            business_id=request.business.id,
            actor_id=request.user.pk,
            **serializer.validated_data,
        ))
        return Response(_operation_data(document), status=status.HTTP_201_CREATED)


class OpeningStockDetailAPIView(OperationDetailAPIView):
    operation_type = InventoryOperation.Type.OPENING_STOCK


class MovementHistoryAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _permission(request, PermissionCode.INVENTORY_VIEW)
        class Query(serializers.Serializer):
            page = serializers.IntegerField(min_value=1, default=1)
            page_size = serializers.IntegerField(min_value=1, max_value=100, default=20)
            warehouse_id = serializers.IntegerField(min_value=1, required=False)
            ingredient_id = serializers.IntegerField(min_value=1, required=False)
            material_type = serializers.ChoiceField(choices=("raw", "compound"), required=False)
            search = serializers.CharField(max_length=200, required=False, allow_blank=True)
            movement_type = serializers.ChoiceField(choices=[item.value for item in MovementType], required=False)
            date_from = serializers.DateField(required=False)
            date_to = serializers.DateField(required=False)
            reference = serializers.CharField(max_length=120, required=False)
            actor_id = serializers.IntegerField(min_value=1, required=False)

            def validate(self, values):
                if values.get("date_from") and values.get("date_to") and values["date_from"] > values["date_to"]:
                    raise serializers.ValidationError({"date_from": "Start date must not be after end date."})
                return values
        query = Query(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        count, rows = operations.movement_history(business_id=request.business.id, **params)
        results = [{
            "id": row.pk, "type": row.movement_type, "direction": row.direction,
            "quantity": str(row.quantity), "unit": row.unit, "unit_cost": str(row.unit_cost),
            "balance_after": str(row.balance_after), "occurred_at": row.occurred_at or row.created_at,
            "warehouse_id": row.stock.warehouse_id, "warehouse_name": row.stock.warehouse.name,
            "ingredient_id": row.stock.ingredient_id, "ingredient_name": row.stock.ingredient.name,
            "material_type": "compound" if row.stock.ingredient.preparation_level == "semi_prepared" else "raw",
            "source_type": row.source_type, "source_document_id": row.source_document_id,
            "source_line_id": row.source_line_id, "operation_kind": row.operation_kind,
            "actor_id": row.actor_id, "reason": row.reason,
        } for row in rows]
        return Response({"count": count, "page": params["page"], "page_size": params["page_size"], "results": results})
