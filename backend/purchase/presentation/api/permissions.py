from rest_framework.exceptions import PermissionDenied


def _purchase_permissions(request) -> list[str]:
    context = getattr(request, "tenant_context", None)
    business_id = getattr(request, "business_id", None)
    permissions = getattr(request, "permissions", None)

    if context is not None and business_id is not None:
        if (
            context.user_id != request.user.id
            or context.business_id != business_id
            or permissions is None
            or tuple(context.permissions) != tuple(permissions)
        ):
            raise PermissionDenied("An active business membership is required.")
        return list(context.permissions)

    membership = getattr(request, "membership", None)
    business = getattr(request, "business", None)
    if (
        membership is None
        or business is None
        or not membership.is_active
        or membership.user_id != request.user.id
        or membership.business_id != business.id
        or membership.role.business_id not in (None, business.id)
        or permissions is None
    ):
        raise PermissionDenied("An active business membership is required.")

    return permissions


def has_purchase_permission(request, permission_code: str) -> bool:
    return permission_code in _purchase_permissions(request)


def require_any_purchase_permission(request, *permission_codes: str) -> None:
    permissions = _purchase_permissions(request)
    if not any(code in permissions for code in permission_codes):
        raise PermissionDenied("You do not have permission to perform this purchase action.")


def require_purchase_permission(request, permission_code: str) -> None:
    """Require a catalog permission from TenantAPIView's server-side context."""

    require_any_purchase_permission(request, permission_code)
