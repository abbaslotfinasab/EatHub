"""Composition root for Accounts application services."""

from accounts.application.change_password import ChangePassword
from accounts.application.business_inventory_settings import UpdateBusinessInventorySettings
from accounts.application.business_onboarding import CreateBusiness
from accounts.application.get_me_read_model import GetMeReadModel
from accounts.application.list_login_memberships import ListLoginMemberships
from accounts.application.login_user import LoginUser
from accounts.application.select_business import SelectBusiness
from accounts.application.tenant_context import TenantContextResolver
from accounts.application.update_business_profile import UpdateBusinessProfile
from accounts.application.update_user_profile import UpdateUserProfile
from accounts.application.user_registration import RegisterUser
from accounts.infrastructure.django.business_inventory_settings_repository import DjangoBusinessInventorySettingsRepository
from accounts.infrastructure.django.business_logo_storage import DjangoBusinessLogoStorage
from accounts.infrastructure.django.business_onboarding_repository import DjangoBusinessOnboardingRepository
from accounts.infrastructure.django.business_profile_update_repository import DjangoBusinessProfileUpdateRepository
from accounts.infrastructure.django.login_token_issuer import DjangoLoginTokenIssuer
from accounts.infrastructure.django.membership_read_repository import DjangoMembershipReadRepository
from accounts.infrastructure.django.password_change_repository import DjangoPasswordChangeRepository
from accounts.infrastructure.django.user_authentication_repository import DjangoUserAuthenticationRepository
from accounts.infrastructure.django.user_avatar_storage import DjangoUserAvatarStorage
from accounts.infrastructure.django.user_profile_update_repository import DjangoUserProfileUpdateRepository
from accounts.infrastructure.django.user_registration_repository import DjangoUserRegistrationRepository
from accounts.infrastructure.django.registration_token_issuer import DjangoRegistrationTokenIssuer


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


def login_user() -> LoginUser:
    return LoginUser(DjangoUserAuthenticationRepository())


def login_token_pair(*, user_id: int) -> tuple[str, str]:
    return DjangoLoginTokenIssuer().issue(user_id=user_id)


def select_business() -> SelectBusiness:
    return SelectBusiness(DjangoMembershipReadRepository())


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


def change_password() -> ChangePassword:
    return ChangePassword(DjangoPasswordChangeRepository())


def register_user() -> RegisterUser:
    return RegisterUser(DjangoUserRegistrationRepository())


def registration_token_pair(*, user_id: int) -> tuple[str, str]:
    return DjangoRegistrationTokenIssuer().issue(user_id=user_id)
