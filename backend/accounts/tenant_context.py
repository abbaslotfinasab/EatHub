from dataclasses import dataclass

from rest_framework.exceptions import APIException
from rest_framework import status

from accounts.models import Membership


@dataclass(frozen=True)
class TenantContext:
    user_id: int
    business_id: int
    membership_id: int
    role_id: int
    permissions: tuple[str, ...]
    business: object
    membership: object


class BusinessContextRequired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        "code": "BUSINESS_CONTEXT_REQUIRED",
        "detail": "X-Business-Id header is required.",
    }
    default_code = "BUSINESS_CONTEXT_REQUIRED"


class BusinessAccessDenied(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = {
        "code": "BUSINESS_ACCESS_DENIED",
        "detail": "The user has no active membership in this business.",
    }
    default_code = "BUSINESS_ACCESS_DENIED"


def resolve_tenant_context(*, user, business_id):
    """Resolve and validate one explicit business context for an authenticated request."""
    if not business_id:
        raise BusinessContextRequired()

    try:
        membership = (
            Membership.objects.select_related("business", "role")
            .get(
                user=user,
                business_id=business_id,
                is_active=True,
                business__is_active=True,
            )
        )
    except (Membership.DoesNotExist, ValueError, TypeError):
        raise BusinessAccessDenied()

    permissions = tuple(
        membership.role.role_permissions.select_related("permission")
        .values_list("permission__code", flat=True)
    )
    return TenantContext(
        user_id=user.pk,
        business_id=membership.business_id,
        membership_id=membership.pk,
        role_id=membership.role_id,
        permissions=permissions,
        business=membership.business,
        membership=membership,
    )
