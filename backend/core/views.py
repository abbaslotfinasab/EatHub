from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.views import TenantAPIView
from core.pagination import DashboardRecentOrdersPagination
from core.serializers.DashboardSerializer import DashboardSerializer
from core.serializers.UploadSerializer import UploadSerializer
from core.services.DashboardService import DashboardService
from core.services.UploadService import UploadService


class UploadAPIView(APIView):

    def post(self, request):

        serializer = UploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = UploadService.upload(
            serializer.validated_data["file"]
        )

        return Response(
            result,
            status=status.HTTP_201_CREATED,
        )


class DashboardAPIView(TenantAPIView):

    def get(self, request):
        data = DashboardService.get_dashboard(
            business=request.business
        )

        paginator = DashboardRecentOrdersPagination()
        recent_orders_page = paginator.paginate_queryset(
            data["recent_orders"],
            request,
            view=self,
        )
        data["recent_orders"] = {
            "count": paginator.page.paginator.count,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": recent_orders_page,
        }

        serializer = DashboardSerializer(data)

        return Response(serializer.data)


