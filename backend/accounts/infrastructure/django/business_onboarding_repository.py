from django.db import transaction

from accounts.application.business_onboarding_result import CreatedBusiness
from accounts.enums import RoleCode
from accounts.infrastructure.django.rbac_initializer import DjangoRBACInitializer
from accounts.models import Business, Membership, Role, User


class DjangoBusinessOnboardingRepository:
    @transaction.atomic
    def create_business_with_owner(
        self, *, user_id: int, name: str, number: str, address: str, logo: str | None
    ) -> CreatedBusiness:
        # Serialize onboarding for one user; membership eligibility is independent
        # from the business selected by any particular browser tab.
        user = User.objects.select_for_update().get(pk=user_id)
        business = Business.objects.create(
            name=name, number=number, address=address, logo=logo, inventory_enabled=False,
        )
        DjangoRBACInitializer.initialize(business)
        owner_role = Role.objects.get(business=business, code=RoleCode.OWNER)
        Membership.objects.create(user=user, business=business, role=owner_role, is_active=True)
        return CreatedBusiness(business_id=business.pk, business_name=business.name)
