"""Composition root for Accounts application services."""

from accounts.application.business_inventory_settings import UpdateBusinessInventorySettings
from accounts.application.business_onboarding import CreateBusiness
from accounts.application.get_me_read_model import GetMeReadModel
from accounts.application.tenant_context import TenantContextResolver
from accounts.infrastructure.django.business_inventory_settings_repository import DjangoBusinessInventorySettingsRepository
from accounts.infrastructure.django.business_onboarding_repository import DjangoBusinessOnboardingRepository
from accounts.infrastructure.django.membership_read_repository import DjangoMembershipReadRepository


def tenant_context_resolver() -> TenantContextResolver:
    return TenantContextResolver(DjangoMembershipReadRepository())


def update_business_inventory_settings() -> UpdateBusinessInventorySettings:
    return UpdateBusinessInventorySettings(DjangoBusinessInventorySettingsRepository())


def create_business() -> CreateBusiness:
    return CreateBusiness(DjangoBusinessOnboardingRepository())


def get_me_read_model() -> GetMeReadModel:
    return GetMeReadModel(DjangoMembershipReadRepository())
