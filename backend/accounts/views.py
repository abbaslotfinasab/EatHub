from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from accounts.serializers.auth_serializer import (
    ChangePasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserMeSerializer,
    UserProfileUpdateSerializer,
)
from accounts.serializers.business_serializer import (
    BusinessCreateSerializer,
    BusinessInventorySettingsSerializer,
    BusinessProfileUpdateSerializer,
    BusinessSerializer,
)
from accounts.application.me_read_model import MeBusinessAccessDeniedError
from accounts.application.select_business import SelectedBusinessNotFoundError
from accounts.application.business_inventory_settings import BusinessInventoryBusinessNotFoundError
from accounts.application.update_business_profile import BusinessProfileNotFoundError
from accounts.application.update_user_profile import (
    UserProfileNotFoundError,
    UserProfileNumberAlreadyInUseError,
)
from accounts.application.change_password import (
    CurrentPasswordInvalidError,
    PasswordChangeUserNotFoundError,
)
from accounts.composition import (
    change_password,
    create_business,
    get_me_read_model,
    login_token_pair,
    registration_token_pair,
    select_business,
    update_business_inventory_settings,
    update_business_profile,
    update_user_profile,
)
from accounts.tenant_context import (
    BusinessAccessDenied,
    get_legacy_membership,
    list_active_memberships,
    resolve_tenant_context,
)


class TenantAPIView(APIView):
    """Legacy tenant base retained for domain endpoints not yet migrated to DTOs.

    Existing single-business clients remain compatible. Multi-business users must
    send X-Business-Id; all selection is validated by the application resolver.
    The isolated legacy adapter supplies ORM models only to these unmigrated views.
    """

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        business_id = request.headers.get("X-Business-Id")
        if not business_id:
            memberships = list_active_memberships(user=request.user, limit=2)
            if not memberships:
                raise PermissionDenied("No active business.")
            if len(memberships) > 1:
                raise ValidationError({
                    "code": "BUSINESS_CONTEXT_REQUIRED",
                    "detail": "X-Business-Id is required when the user has multiple active businesses.",
                })
            business_id = memberships[0].business_id

        context = resolve_tenant_context(user=request.user, business_id=business_id)
        membership = get_legacy_membership(user=request.user, business_id=context.business_id)
        request.tenant_context = context
        request.business = membership.business
        request.membership = membership
        request.role = membership.role
        request.permissions = list(context.permissions)


class ExplicitTenantAPIView(APIView):
    """Legacy explicit tenant base for domain endpoints awaiting DTO migration."""

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        context = resolve_tenant_context(
            user=request.user,
            business_id=request.headers.get("X-Business-Id"),
        )
        membership = get_legacy_membership(user=request.user, business_id=context.business_id)
        request.tenant_context = context
        request.business = membership.business
        request.membership = membership
        request.role = membership.role
        request.permissions = list(context.permissions)


class ApplicationTenantAPIView(APIView):
    """DTO-only tenant base with legacy single-business selection behavior."""

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        business_id = request.headers.get("X-Business-Id")
        if not business_id:
            memberships = list_active_memberships(user=request.user, limit=2)
            if not memberships:
                raise PermissionDenied("No active business.")
            if len(memberships) > 1:
                raise ValidationError({
                    "code": "BUSINESS_CONTEXT_REQUIRED",
                    "detail": "X-Business-Id is required when the user has multiple active businesses.",
                })
            business_id = memberships[0].business_id

        context = resolve_tenant_context(user=request.user, business_id=business_id)
        request.tenant_context = context
        request.business_id = context.business_id
        request.role_code = context.role_code
        request.permissions = list(context.permissions)


class ExplicitApplicationTenantAPIView(APIView):
    """Require explicit tenant selection and expose only scalar DTO context."""

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        context = resolve_tenant_context(
            user=request.user,
            business_id=request.headers.get("X-Business-Id"),
        )
        request.tenant_context = context
        request.business_id = context.business_id
        request.role_code = context.role_code
        request.permissions = list(context.permissions)


class RegisterAPIView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        access, refresh = registration_token_pair(user_id=user.user_id)
        return Response({
            "user": {
                "id": user.user_id,
                "email": user.email,
                "name": user.name,
                "number": user.number,
            },
            "access": access,
            "refresh": refresh,
        })


class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = data["user"]
        memberships = data["memberships"]
        access, refresh = login_token_pair(user_id=user.user_id)
        return Response({
            "user": {
                "id": user.user_id,
                "name": user.name,
                "number": user.number,
                "email": user.email,
            },
            "access": access,
            "refresh": refresh,
            "businesses": [
                {
                    "id": membership.business_id,
                    "name": membership.business_name,
                    "role": membership.role,
                }
                for membership in memberships
            ],
        })


class SelectBusinessAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        business_id = request.data.get("business_id")
        if not business_id:
            raise ValidationError({"business_id": "This field is required."})

        try:
            selected = select_business().execute(
                user_id=request.user.pk,
                business_id=business_id,
            )
        except SelectedBusinessNotFoundError:
            return Response({"detail": "Invalid or inactive business membership"}, status=400)

        return Response({
            "business": {
                "id": selected.business_id,
                "name": selected.business_name,
            },
            "role": selected.role,
        })


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def _serialize(self, request):
        try:
            context = get_me_read_model().execute(
                user_id=request.user.pk,
                business_id=request.headers.get("X-Business-Id"),
            )
        except MeBusinessAccessDeniedError:
            raise BusinessAccessDenied()

        user = request.user
        return UserMeSerializer({
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "number": user.number,
            "avatar": user.avatar,
            "has_business": context.has_business,
            "active_business": context.active_business,
            "memberships": context.memberships,
            "meta": {
                "needs_onboarding": context.needs_onboarding,
                "business_count": context.business_count,
            },
        }, context={"request": request}).data

    def get(self, request):
        return Response(self._serialize(request))

    def patch(self, request):
        serializer = UserProfileUpdateSerializer(
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        changes = serializer.validated_data
        update_kwargs = {}
        if "name" in changes:
            update_kwargs["name"] = changes["name"]
        if "number" in changes:
            update_kwargs["number"] = changes["number"]
        if "avatar" in changes:
            update_kwargs["avatar_path"] = changes["avatar"]
        try:
            update_user_profile().execute(
                user_id=request.user.pk,
                **update_kwargs,
            )
        except UserProfileNumberAlreadyInUseError:
            raise ValidationError({"number": "This field must be unique."})
        except UserProfileNotFoundError:
            raise NotFound("User not found.")
        request.user.refresh_from_db(fields=["name", "number", "avatar"])
        return Response(self._serialize(request))


class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            change_password().execute(
                user_id=request.user.pk,
                old_password=serializer.validated_data["old_password"],
                new_password=serializer.validated_data["new_password"],
            )
        except CurrentPasswordInvalidError:
            raise ValidationError({
                "old_password": "رمز عبور فعلی صحیح نیست."
            })
        except PasswordChangeUserNotFoundError:
            raise NotFound("User not found.")
        return Response({"detail": "رمز عبور با موفقیت تغییر کرد."})


class BusinessCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BusinessCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        business = create_business().execute(
            user_id=request.user.pk,
            name=serializer.validated_data["name"],
            number=serializer.validated_data.get("number", ""),
            address=serializer.validated_data.get("address", ""),
            logo=serializer.validated_data.get("logo"),
        )
        return Response({
            "id": business.business_id,
            "name": business.business_name,
            "active_business": {
                "id": business.business_id,
                "name": business.business_name,
                "role": "owner",
            },
        })


class BusinessProfileAPIView(ApplicationTenantAPIView):
    permission_classes = [IsAuthenticated]

    def _ensure_owner(self, request):
        if request.role_code != "OWNER":
            raise PermissionDenied("Only the business owner can update business details.")

    def get(self, request):
        return Response(BusinessSerializer(
            request.tenant_context.business,
            context={"request": request},
        ).data)

    def patch(self, request):
        self._ensure_owner(request)
        serializer = BusinessProfileUpdateSerializer(
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        changes = serializer.validated_data
        update_kwargs = {}
        if "name" in changes:
            update_kwargs["name"] = changes["name"]
        if "number" in changes:
            update_kwargs["number"] = changes["number"]
        if "address" in changes:
            update_kwargs["address"] = changes["address"]
        if "logo" in changes:
            update_kwargs["logo_path"] = changes["logo"] or None
        try:
            update_business_profile().execute(
                business_id=request.business_id,
                **update_kwargs,
            )
        except BusinessProfileNotFoundError:
            raise NotFound("Business not found.")

        context = resolve_tenant_context(
            user=request.user,
            business_id=request.business_id,
        )
        request.tenant_context = context
        return Response(BusinessSerializer(
            context.business,
            context={"request": request},
        ).data)


class BusinessInventorySettingsAPIView(ExplicitApplicationTenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "inventory_enabled": request.tenant_context.business.inventory_enabled
        })

    def patch(self, request):
        if request.role_code != "OWNER":
            raise PermissionDenied("Only the business owner can change inventory settings.")
        serializer = BusinessInventorySettingsSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            inventory_enabled = update_business_inventory_settings().execute(
                business_id=request.business_id,
                inventory_enabled=serializer.validated_data.get(
                    "inventory_enabled",
                    request.tenant_context.business.inventory_enabled,
                ),
            )
        except BusinessInventoryBusinessNotFoundError:
            raise NotFound("Business not found.")
        return Response({"inventory_enabled": inventory_enabled})
