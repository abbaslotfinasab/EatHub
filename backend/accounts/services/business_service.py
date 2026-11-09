from django.db import transaction

from accounts.enums import RoleCode
from accounts.models import Business, Membership, Role, User
from accounts.services.rbac_initializer import RBACInitializer


class BusinessService:

    @staticmethod
    @transaction.atomic
    def create_business(user, name, number="", address="", logo=None, request=None):
        # Serialize onboarding for one user; membership eligibility is independent
        # from the business selected by any particular browser tab.
        User.objects.select_for_update().get(pk=user.pk)

        business = Business.objects.create(
            name=name,
            number=number,
            address=address,
            logo=logo,
            inventory_enabled=False,
        )

        RBACInitializer.initialize(business)

        owner_role = Role.objects.get(
            business=business,
            code=RoleCode.OWNER
        )

        Membership.objects.create(
            user=user,
            business=business,
            role=owner_role,
            is_active=True
        )

        return business
