"""Composition root for Accounts application services."""

from accounts.application.tenant_context import TenantContextResolver
from accounts.infrastructure.django.membership_read_repository import (
    DjangoMembershipReadRepository,
)


def tenant_context_resolver() -> TenantContextResolver:
    return TenantContextResolver(DjangoMembershipReadRepository())

from accounts.application.business_inventory_settings import (
    UpdateBusinessInventorySettings,
)
from accounts.infrastructure.django.business_inventory_settings_repository import (
    DjangoBusinessInventorySettingsRepository,
)


def update_business_inventory_settings() -> UpdateBusinessInventorySettings:
    return UpdateBusinessInventorySettings(DjangoBusinessInventorySettingsRepository())
