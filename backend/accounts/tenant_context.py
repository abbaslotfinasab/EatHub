from rest_framework import status
from rest_framework.exceptions import APIException

from accounts.application.tenant_context import (
    BusinessAccessDeniedError,
    BusinessContextRequiredError,
    TenantContext,
)
from accounts.composition import legacy_tenant_context_adapter, tenant_context_resolver


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


def resolve_tenant_context(*, user, business_id) -> TenantContext:
    """Translate application errors while keeping the returned context DTO-only."""
    try:
        return tenant_context_resolver().resolve(
            user_id=user.pk,
            business_id=business_id,
        )
    except BusinessContextRequiredError:
        raise BusinessContextRequired()
    except BusinessAccessDeniedError:
        raise BusinessAccessDenied()


def list_active_memberships(*, user, limit=2):
    return tenant_context_resolver().list_active_memberships(
        user_id=user.pk,
        limit=limit,
    )


def get_active_membership(*, user, business_id):
    return tenant_context_resolver().get_active_membership(
        user_id=user.pk,
        business_id=business_id,
    )


def get_legacy_membership(*, user, business_id):
    """Explicit compatibility bridge for endpoints still consuming Django models."""
    membership = legacy_tenant_context_adapter().get_active_membership(
        user_id=user.pk,
        business_id=business_id,
    )
    if membership is None:
        raise BusinessAccessDenied()
    return membership


def get_role_permission_codes(*, role_id):
    return tenant_context_resolver().list_role_permission_codes(role_id=role_id)
