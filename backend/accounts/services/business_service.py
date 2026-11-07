from django.db import transaction

from accounts.enums import RoleCode
from accounts.models import Business, Membership, Role, User
from accounts.services.rbac_initializer import RBACInitializer


class BusinessService:

    @staticmethod
    @transaction.atomic
    def create_business(user, name, number="", address="", logo=None, request=None):
        # Serialize business creation per user so the partial unique constraint
        # (one active business per user) remains valid under concurrent requests.
        User.objects.select_for_update().get(pk=user.pk)
        Membership.objects.filter(user=user, is_active=True).update(is_active=False)

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
