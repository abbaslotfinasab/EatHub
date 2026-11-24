"""Composition root for Accounts application services."""

from accounts.application.tenant_context import TenantContextResolver
from accounts.infrastructure.django.membership_read_repository import (
    DjangoMembershipReadRepository,
)


def tenant_context_resolver() -> TenantContextResolver:
    return TenantContextResolver(DjangoMembershipReadRepository())
