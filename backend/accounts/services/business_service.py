from django.db import transaction

from accounts.enums import RoleCode
from accounts.models import Business, Membership, Role
from accounts.services.rbac_initializer import RBACInitializer


class BusinessService:

    @staticmethod
    @transaction.atomic
    def create_business(user, name):

        business = Business.objects.create(
            name=name,
            slug=name.lower().replace(" ", "-"),
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