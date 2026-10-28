from rest_framework import serializers, status
from rest_framework.exceptions import APIException, NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.views import TenantAPIView
from core.enums import PermissionCode
from inventory.application.context import InventoryExecutionContext
from inventory.application.exceptions import InvalidApplicationInput, OperationConflict, ResourceNotFound
from inventory.application.use_cases.manage_reservations import ManageReservations
from inventory.domain.entities.reservation import MANUAL_RESERVATION_SOURCE
from inventory.domain.enums.reservation import ReservationStatus
from inventory.domain.exceptions import InventoryDomainError
from inventory.domain.value_objects.unit import Unit
from inventory.infrastructure.django.reservation_repository import DjangoReservationRepository
from inventory.infrastructure.django.unit_of_work import DjangoInventoryUnitOfWork


MAX_POSITIVE_BIG_INTEGER = 9_223_372_036_854_775_807


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if hasattr(data, "keys"):
            unknown = set(data.keys()) - set(self.fields.keys())
            if unknown:
                raise serializers.ValidationError({key: "Unknown field." for key in sorted(unknown)})
        return super().to_internal_value(data)


class PositiveBigIntegerIdentifierField(serializers.IntegerField):
    """Accept exact integer IDs only within Django's signed bigint range."""

    def __init__(self, **kwargs):
        kwargs.setdefault("min_value", 1)
        kwargs.setdefault("max_value", MAX_POSITIVE_BIG_INTEGER)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        if isinstance(data, bool) or isinstance(data, float):
            raise serializers.ValidationError("A whole-number identifier is required.")
        if isinstance(data, str):
            normalized = data.strip()
            if not normalized.isascii() or not normalized.isdigit():
                raise serializers.ValidationError("A whole-number identifier is required.")
            data = normalized
        elif not isinstance(data, int):
            raise serializers.ValidationError("A whole-number identifier is required.")
        return super().to_internal_value(data)


class ReservationLineInputSerializer(StrictSerializer):
    ingredient_id = serializers.IntegerField(min_value=1)
    source_line_id = PositiveBigIntegerIdentifierField(required=False)
    quantity = serializers.DecimalField(max_digits=36, decimal_places=12, min_value=0)
    unit = serializers.ChoiceField(choices=[unit.value for unit in Unit], required=False)

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be positive.")
        return value


class ReservationCreateSerializer(StrictSerializer):
    warehouse_id = serializers.IntegerField(min_value=1)
    source_type = serializers.ChoiceField(
        choices=(MANUAL_RESERVATION_SOURCE,), required=False, default=MANUAL_RESERVATION_SOURCE
    )
    source_id = PositiveBigIntegerIdentifierField(required=False, allow_null=True)
    reason = serializers.CharField(max_length=500, allow_blank=False, trim_whitespace=True)
    idempotency_key = serializers.UUIDField()
    lines = ReservationLineInputSerializer(many=True, allow_empty=False)

    def validate(self, attrs):
        if attrs.get("source_id") is not None:
            raise serializers.ValidationError({
                "source_id": "Manual reservations cannot reference an external source ID."
            })
        if any(line.get("source_line_id") is not None for line in attrs["lines"]):
            raise serializers.ValidationError({
                "lines": "Manual reservations cannot reference external source lines."
            })
        return attrs


class ReservationReleaseSerializer(StrictSerializer):
    idempotency_key = serializers.UUIDField()
    reason = serializers.CharField(max_length=500, allow_blank=False, trim_whitespace=True)


class ReservationListQuerySerializer(serializers.Serializer):
    source_type = serializers.RegexField(r"^[a-z][a-z0-9_.-]{0,63}$", required=False)
    source_id = PositiveBigIntegerIdentifierField(required=False)
    status = serializers.ChoiceField(choices=[item.value for item in ReservationStatus], required=False)
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, required=False, default=20)


class AvailabilityQuerySerializer(serializers.Serializer):
    warehouse_id = serializers.IntegerField(min_value=1)
    ingredient_id = serializers.IntegerField(min_value=1)


class ConflictResponse(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The Inventory reservation conflicts with its current state."


def _use_case():
    return ManageReservations(
        DjangoReservationRepository(),
        DjangoInventoryUnitOfWork(),
    )


def _permission(request, code):
    if code.value not in request.permissions:
        raise PermissionDenied("You do not have permission for this Inventory operation.")


def _run(call):
    try:
        return call()
    except ResourceNotFound as error:
        raise NotFound(str(error)) from error
    except OperationConflict as error:
        raise ConflictResponse(str(error)) from error
    except (InvalidApplicationInput, InventoryDomainError, ValueError) as error:
        raise serializers.ValidationError({"detail": str(error)}) from error


def _line_data(line):
    return {
        "id": line.id,
        "ingredient_id": line.ingredient_id,
        "ingredient_name": line.ingredient_name,
        "source_line_id": line.source_line_id,
        "quantity": str(line.quantity),
        "unit": line.unit.value,
    }


def _reservation_data(reservation):
    return {
        "id": reservation.id,
        "warehouse_id": reservation.warehouse_id,
        "warehouse_name": reservation.warehouse_name,
        "source_type": reservation.source_type,
        "source_id": reservation.source_id,
        "reason": reservation.reason,
        "status": reservation.status.value,
        "idempotency_key": reservation.idempotency_key,
        "created_by_id": reservation.created_by_id,
        "released_by_id": reservation.released_by_id,
        "released_at": reservation.released_at,
        "release_reason": reservation.release_reason,
        "created_at": reservation.created_at,
        "updated_at": reservation.updated_at,
        "lines": [_line_data(line) for line in reservation.lines],
    }


class ReservationListCreateAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _permission(request, PermissionCode.INVENTORY_VIEW)
        query = ReservationListQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        count, rows = _use_case().list(
            InventoryExecutionContext(request.business.id, request.user.pk),
            **query.validated_data,
        )
        return Response({
            "count": count,
            "page": query.validated_data["page"],
            "page_size": query.validated_data["page_size"],
            "results": [_reservation_data(row) for row in rows],
        })

    def post(self, request):
        _permission(request, PermissionCode.INVENTORY_ADJUST)
        serializer = ReservationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reservation = _run(lambda: _use_case().create(
            InventoryExecutionContext(request.business.id, request.user.pk),
            **serializer.validated_data,
        ))
        return Response(_reservation_data(reservation), status=status.HTTP_201_CREATED)


class ReservationDetailAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, action=None):
        _permission(request, PermissionCode.INVENTORY_VIEW)
        if action is not None:
            raise NotFound("Reservation action was not found.")
        result = _run(lambda: _use_case().get(
            InventoryExecutionContext(request.business.id, request.user.pk), pk
        ))
        return Response(_reservation_data(result))

    def post(self, request, pk, action=None):
        _permission(request, PermissionCode.INVENTORY_ADJUST)
        if action != "release":
            raise NotFound("Reservation action was not found.")
        serializer = ReservationReleaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = _run(lambda: _use_case().release(
            InventoryExecutionContext(request.business.id, request.user.pk),
            pk,
            **serializer.validated_data,
        ))
        return Response(_reservation_data(result))


class ReservationAvailabilityAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _permission(request, PermissionCode.INVENTORY_VIEW)
        query = AvailabilityQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        result = _run(lambda: _use_case().availability(
            InventoryExecutionContext(request.business.id, request.user.pk),
            **query.validated_data,
        ))
        return Response({
            "warehouse_id": result.warehouse_id,
            "ingredient_id": result.ingredient_id,
            "ingredient_name": result.ingredient_name,
            "physical_quantity": str(result.physical_quantity),
            "reserved_quantity": str(result.reserved_quantity),
            "available_quantity": str(result.available_quantity),
            "unit": result.unit.value,
        })
