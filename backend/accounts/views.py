from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from accounts.models import Membership, User
from accounts.serializers.auth_serializer import (
    ChangePasswordSerializer,
    RegisterSerializer,
    UserMeSerializer,
    UserListSerializer,
    UserProfileUpdateSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.serializers.auth_serializer import LoginSerializer
from accounts.serializers.business_serializer import (
    BusinessCreateSerializer,
    BusinessInventorySettingsSerializer,
    BusinessProfileUpdateSerializer,
    BusinessSerializer,
)
from accounts.services.business_service import BusinessService
from accounts.services.me_service import MeService
from accounts.tenant_context import resolve_tenant_context


class TenantAPIView(APIView):
    """Compatibility tenant base with explicit selection for multi-business users.

    Existing single-business clients remain compatible during the route migration.
    Multi-business users must send X-Business-Id; it is always validated server-side.
    New endpoints should use ExplicitTenantAPIView directly.
    """

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        business_id = request.headers.get("X-Business-Id")
        if business_id:
            context = resolve_tenant_context(
                user=request.user,
                business_id=business_id,
            )
            request.tenant_context = context
            request.business = context.business
            request.membership = context.membership
            request.role = context.membership.role
            request.permissions = list(context.permissions)
            return

        memberships = list(
            Membership.objects.select_related("business", "role")
            .filter(user=request.user, is_active=True, business__is_active=True)
            .order_by("id")[:2]
        )
        if not memberships:
            raise PermissionDenied("No active business.")
        if len(memberships) > 1:
            raise ValidationError({
                "code": "BUSINESS_CONTEXT_REQUIRED",
                "detail": "X-Business-Id is required when the user has multiple active businesses.",
            })

        membership = memberships[0]
        request.business = membership.business
        request.membership = membership
        request.role = membership.role
        request.permissions = list(
            membership.role.role_permissions.select_related("permission")
            .values_list("permission__code", flat=True)
        )


class ExplicitTenantAPIView(APIView):
    """Require an explicit, authorized business context from X-Business-Id."""

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        context = resolve_tenant_context(
            user=request.user,
            business_id=request.headers.get("X-Business-Id"),
        )
        request.tenant_context = context
        request.business = context.business
        request.membership = context.membership
        request.role = context.membership.role
        request.permissions = list(context.permissions)


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
                {"id": m.business.id, "name": m.business.name, "role": m.role.code}
                for m in memberships
            ],
        })


class SelectBusinessAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        business_id = request.data.get("business_id")
        if not business_id:
            raise ValidationError({"business_id": "This field is required."})

        try:
            new_membership = Membership.objects.select_related(
                "business", "role"
            ).get(
                user=request.user,
                business_id=business_id,
                is_active=True,
                business__is_active=True,
            )
        except Membership.DoesNotExist:
            return Response({"detail": "Invalid or inactive business membership"}, status=400)

        return Response({
            "business": {
                "id": new_membership.business.id,
                "name": new_membership.business.name,
            },
            "role": new_membership.role.code,
        })

class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def _serialize(self, request):
        context = MeService.get_user_context(request.user, request=request)
        user = context["user"]
        return UserMeSerializer({
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "number": user.number,
            "avatar": user.avatar,
            "has_business": context["has_business"],
            "active_business": context["active_business"],
            "memberships": context["memberships"],
            "meta": context["meta"],
        }, context={"request": request}).data

    def get(self, request):
        return Response(self._serialize(request))

    def patch(self, request):
        serializer = UserProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(self._serialize(request))


class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return Response({"detail": "رمز عبور با موفقیت تغییر کرد."})


class BusinessCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BusinessCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        business = BusinessService.create_business(
            user=request.user,
            name=serializer.validated_data["name"],
            number=serializer.validated_data.get("number", ""),
            address=serializer.validated_data.get("address", ""),
            logo=serializer.validated_data.get("logo"),
            request=request,
        )
        return Response({
            "id": business.id,
            "name": business.name,
            "active_business": {
                "id": business.id,
                "name": business.name,
                "role": "owner",
            },
        })


class UserListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = User.objects.all().order_by("-id")
        serializer = UserListSerializer(users, many=True, context={"request": request})
        return Response(serializer.data)


class BusinessProfileAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def _ensure_owner(self, request):
        if request.role.code != "OWNER":
            raise PermissionDenied("Only the business owner can update business details.")

    def get(self, request):
        return Response(BusinessSerializer(request.business, context={"request": request}).data)

    def patch(self, request):
        self._ensure_owner(request)
        serializer = BusinessProfileUpdateSerializer(
            request.business,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        business = serializer.save()
        return Response(BusinessSerializer(business, context={"request": request}).data)


class BusinessInventorySettingsAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"inventory_enabled": request.business.inventory_enabled})

    def patch(self, request):
        if request.role.code != "OWNER":
            raise PermissionDenied("Only the business owner can change inventory settings.")
        serializer = BusinessInventorySettingsSerializer(request.business, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"inventory_enabled": request.business.inventory_enabled})
