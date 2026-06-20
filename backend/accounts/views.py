from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from accounts.enums import RoleCode
from accounts.models import Membership
from accounts.serializers.auth_serializer import RegisterSerializer, UserMeSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.serializers.auth_serializer import LoginSerializer
from accounts.serializers.business_serializer import BusinessCreateSerializer
from accounts.services.business_service import BusinessService
from accounts.services.me_service import MeService


class RegisterAPIView(APIView):

    def post(self, request):

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "number": user.number,

            },
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })

class LoginAPIView(APIView):

    def post(self, request):

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        user = data["user"]
        memberships = data["memberships"]

        refresh = RefreshToken.for_user(user)

        return Response({
            "user": {
                "id": user.id,
                "name" : user.name,
                "number": user.number,
                "email": user.email,
            },
            "access": str(refresh.access_token),
            "refresh": str(refresh),

            "businesses": [
                {
                    "id": m.business.id,
                    "name": m.business.name,
                    "role": m.role.code
                }
                for m in memberships
            ]
        })


class SelectBusinessAPIView(APIView):

    def post(self, request):

        business_id = request.data.get("business_id")

        memberships = request.user.memberships.filter(
            business_id=business_id,
            is_active=True
        ).select_related("business", "role")

        membership = memberships.first()

        if not membership:
            return Response({"detail": "Invalid business"}, status=400)

        return Response({
            "business": {
                "id": membership.business.id,
                "name": membership.business.name,
            },
            "role": membership.role.code
        })


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]


    def get(self, request):
        context = MeService.get_user_context(
            request.user,
            request=request
        )

        serializer = UserMeSerializer(
            {
                "id": context["user"].id,
                "email": context["user"].email,
                "name": context["user"].name,
                "number": context["user"].number,
                "has_business": context["has_business"],
                "active_business": context["active_business"],
                "memberships": context["memberships"],
                "meta": context["meta"],
            },
            context={"request": request}
        )

        return Response(serializer.data)



class BusinessCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BusinessCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        business = BusinessService.create_business(
            user=request.user,
            name=serializer.validated_data["name"]
        )

        return Response({
            "id": business.id,
            "name": business.name,
            "active_business": {
                "id": business.id,
                "name": business.name,
                "role": "owner"
            }
        })