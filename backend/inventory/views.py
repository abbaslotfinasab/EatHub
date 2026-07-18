from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.views import TenantAPIView
from inventory.models import PurchaseOrder
from inventory.serializers.facture_serializer import PurchaseOrderStatusUpdateSerializer, PurchaseOrderSerializer, \
    UpdatePurchaseOrderInputSerializer, CreatePurchaseOrderInputSerializer
from inventory.services.facture_service import PurchaseOrderService


class PurchaseOrderCreateAPIView(TenantAPIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = CreatePurchaseOrderInputSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        purchase_order = PurchaseOrderService.create_purchase_order(
            business=request.business,
            validated_data=serializer.validated_data,
        )

        return Response(
            PurchaseOrderSerializer(
                purchase_order
            ).data,
            status=status.HTTP_201_CREATED,
        )


class PurchaseOrderListAPIView(TenantAPIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        purchase_orders = (
            PurchaseOrder.objects
            .filter(
                business=request.business
            )
            .prefetch_related(
                "items"
            )
            .order_by(
                "-created_at"
            )
        )

        return Response(
            PurchaseOrderSerializer(
                purchase_orders,
                many=True,
            ).data
        )


class PurchaseOrderDetailAPIView(TenantAPIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        purchase_order = get_object_or_404(
            PurchaseOrder.objects.prefetch_related(
                "items"
            ),
            pk=pk,
            business=request.business,
        )

        return Response(
            PurchaseOrderSerializer(
                purchase_order
            ).data
        )


class PurchaseOrderUpdateAPIView(TenantAPIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):

        purchase_order = get_object_or_404(
            PurchaseOrder,
            pk=pk,
            business=request.business,
        )

        serializer = UpdatePurchaseOrderInputSerializer(
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        purchase_order = PurchaseOrderService.update_purchase_order(
            purchase_order=purchase_order,
            validated_data=serializer.validated_data,
        )

        return Response(
            PurchaseOrderSerializer(
                purchase_order
            ).data
        )


class PurchaseOrderDeleteAPIView(TenantAPIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):

        purchase_order = get_object_or_404(
            PurchaseOrder,
            pk=pk,
            business=request.business,
        )

        PurchaseOrderService.delete_purchase_order(
            purchase_order
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class PurchaseOrderStatusUpdateAPIView(TenantAPIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        purchase_order = get_object_or_404(
            PurchaseOrder,
            pk=pk,
            business=request.business,
        )

        serializer = PurchaseOrderStatusUpdateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        purchase_order = PurchaseOrderService.update_status(
            purchase_order=purchase_order,
            status=serializer.validated_data["status"],
        )

        return Response(
            PurchaseOrderSerializer(
                purchase_order
            ).data
        )