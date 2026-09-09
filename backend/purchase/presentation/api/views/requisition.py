from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.views import TenantAPIView
from purchase.application.dto.requisition import (
    CreateRequisitionDTO,
    CreateRequisitionItemDTO,
    ListRequisitionsQuery,
)
from purchase.application.use_cases.requisition.approve_requisition import (
    ApproveRequisitionUseCase,
)
from purchase.application.use_cases.requisition.create_requisition import (
    CreateRequisitionUseCase,
)
from purchase.application.use_cases.requisition.get_requisition import (
    GetRequisitionUseCase,
)
from purchase.application.use_cases.requisition.list_requisitions import (
    ListRequisitionsUseCase,
)
from purchase.application.use_cases.requisition.reject_requisition import (
    RejectRequisitionUseCase,
)
from purchase.application.use_cases.requisition.submit_requisition import (
    SubmitRequisitionUseCase,
)
from purchase.domain.enums.requisition_status import RequisitionStatus
from purchase.infrastructure.persistence.django.repositories.requisition_repository import (
    DjangoRequisitionRepository,
)
from purchase.presentation.api.serializers.requisition import (
    CreateRequisitionSerializer,
    RequisitionSerializer,
)


def _requisition_repository() -> DjangoRequisitionRepository:
    return DjangoRequisitionRepository()


def _parse_status(value: str | None) -> RequisitionStatus | None:
    if value is None or value == "":
        return None

    try:
        return RequisitionStatus(value)
    except ValueError as error:
        raise ValidationError(
            {"status": "Must be a valid requisition status."}
        ) from error


def _handle_requisition_error(error: ValueError) -> None:
    detail = str(error)

    if "does not exist" in detail:
        raise NotFound({"detail": detail})

    raise ValidationError({"detail": detail})


class RequisitionListCreateAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            requisitions = ListRequisitionsUseCase(
                _requisition_repository()
            ).execute(
                ListRequisitionsQuery(
                    business_id=request.business.id,
                    status=_parse_status(request.query_params.get("status")),
                )
            )
        except ValueError as error:
            _handle_requisition_error(error)

        return Response(RequisitionSerializer(requisitions, many=True).data)

    def post(self, request):
        serializer = CreateRequisitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            requisition = CreateRequisitionUseCase(
                _requisition_repository()
            ).execute(
                CreateRequisitionDTO(
                    business_id=request.business.id,
                    requested_by_id=request.user.id,
                    reason=data.get("reason", ""),
                    items=[
                        CreateRequisitionItemDTO(
                            ingredient_id=item["ingredient_id"],
                            quantity=item["quantity"],
                            note=item.get("note", ""),
                        )
                        for item in data["items"]
                    ],
                )
            )
        except ValueError as error:
            _handle_requisition_error(error)

        return Response(
            RequisitionSerializer(requisition).data,
            status=status.HTTP_201_CREATED,
        )


class RequisitionDetailAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            requisition = GetRequisitionUseCase(
                _requisition_repository()
            ).execute(
                requisition_id=pk,
                business_id=request.business.id,
            )
        except ValueError as error:
            _handle_requisition_error(error)

        return Response(RequisitionSerializer(requisition).data)


class RequisitionSubmitAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return _transition_response(
            SubmitRequisitionUseCase,
            requisition_id=pk,
            business_id=request.business.id,
        )


class RequisitionApproveAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return _transition_response(
            ApproveRequisitionUseCase,
            requisition_id=pk,
            business_id=request.business.id,
        )


class RequisitionRejectAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return _transition_response(
            RejectRequisitionUseCase,
            requisition_id=pk,
            business_id=request.business.id,
        )


def _transition_response(
    use_case_type,
    *,
    requisition_id: int,
    business_id: int,
) -> Response:
    try:
        requisition = use_case_type(_requisition_repository()).execute(
            requisition_id=requisition_id,
            business_id=business_id,
        )
    except ValueError as error:
        _handle_requisition_error(error)

    return Response(RequisitionSerializer(requisition).data)
