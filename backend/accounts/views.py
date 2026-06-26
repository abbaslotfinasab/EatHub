from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from accounts.models import Membership, User
from accounts.serializers.auth_serializer import RegisterSerializer, UserMeSerializer, UserListSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.serializers.auth_serializer import LoginSerializer
from accounts.serializers.business_serializer import BusinessCreateSerializer
from accounts.services.business_service import BusinessService
from accounts.services.me_service import MeService


class TenantAPIView(APIView):

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        membership = (
            Membership.objects
            .select_related("business", "role")
            .filter(
                user=request.user,
                is_active=True,
            )
            .first()
        )

        if not membership:
            raise PermissionDenied("No active business.")

        request.business = membership.business
        request.membership = membership
        request.role = membership.role
        request.permissions = list(
            membership.role.role_permissions.select_related("permission")
            .values_list("permission__code", flat=True)
        )


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
                "name": user.name,
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

    @transaction.atomic
    def post(self, request):
        business_id = request.data.get("business_id")

        if not business_id:
            raise ValidationError({
                "business_id": "This field is required."
            })

        # گرفتن membership هدف
        try:
            new_membership = Membership.objects.select_related(
                "business",
                "role",
            ).get(
                user=request.user,
                business_id=business_id,
            )
        except Membership.DoesNotExist:
            return Response(
                {"detail": "Invalid business"},
                status=400
            )

        # غیرفعال کردن قبلی‌ها
        Membership.objects.filter(
            user=request.user,
            is_active=True
        ).update(is_active=False)

        # فعال کردن جدید
        new_membership.is_active = True
        new_membership.save(update_fields=["is_active"])

        return Response({
            "business": {
                "id": new_membership.business.id,
                "name": new_membership.business.name,
            },
            "role": new_membership.role.code
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
            name=serializer.validated_data["name"],
            request=request
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


class UserListAPIView(APIView):

    def get(self, request):
        users = User.objects.all().order_by("-id")

        serializer = UserListSerializer(
            users,
            many=True
        )

        return Response(serializer.data)
