"""Composition root for Accounts application services."""

from accounts.application.business_inventory_settings import UpdateBusinessInventorySettings
from accounts.application.business_onboarding import CreateBusiness
from accounts.application.get_me_read_model import GetMeReadModel
from accounts.application.list_login_memberships import ListLoginMemberships
from accounts.application.tenant_context import TenantContextResolver
from accounts.application.update_business_profile import UpdateBusinessProfile
from accounts.application.update_user_profile import UpdateUserProfile
from accounts.infrastructure.django.business_inventory_settings_repository import DjangoBusinessInventorySettingsRepository
from accounts.infrastructure.django.business_logo_storage import DjangoBusinessLogoStorage
from accounts.infrastructure.django.business_onboarding_repository import DjangoBusinessOnboardingRepository
from accounts.infrastructure.django.business_profile_update_repository import DjangoBusinessProfileUpdateRepository
from accounts.infrastructure.django.membership_read_repository import DjangoMembershipReadRepository
from accounts.infrastructure.django.user_avatar_storage import DjangoUserAvatarStorage
from accounts.infrastructure.django.user_profile_update_repository import DjangoUserProfileUpdateRepository


def tenant_context_resolver() -> TenantContextResolver:
    return TenantContextResolver(DjangoMembershipReadRepository())


def update_business_inventory_settings() -> UpdateBusinessInventorySettings:
    return UpdateBusinessInventorySettings(DjangoBusinessInventorySettingsRepository())


def create_business() -> CreateBusiness:
    return CreateBusiness(DjangoBusinessOnboardingRepository())


def get_me_read_model() -> GetMeReadModel:
    return GetMeReadModel(DjangoMembershipReadRepository())


def list_login_memberships() -> ListLoginMemberships:
    return ListLoginMemberships(DjangoMembershipReadRepository())


def update_user_profile() -> UpdateUserProfile:
    return UpdateUserProfile(
        DjangoUserProfileUpdateRepository(),
        DjangoUserAvatarStorage(),
    )


def update_business_profile() -> UpdateBusinessProfile:
    return UpdateBusinessProfile(
        DjangoBusinessProfileUpdateRepository(),
        DjangoBusinessLogoStorage(),
    )
