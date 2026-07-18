from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


from core.serializers.UploadSerializer import UploadSerializer
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