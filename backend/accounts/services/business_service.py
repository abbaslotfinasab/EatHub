from django.db import transaction
from django.urls import reverse

from accounts.enums import RoleCode
from accounts.models import Business, Membership, Role
from accounts.services.qr_service import QRService
from accounts.services.rbac_initializer import RBACInitializer


class BusinessService:

    @staticmethod
    @transaction.atomic
    def create_business(user, name,request=None
):

        business = Business.objects.create(
            name=name,
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

        QRService.generate_qr_for_business(
            business,
            request=request
        )


        return business

    @staticmethod
    def build_public_url(business):
        path = reverse("products:public-menu", kwargs={"slug": business.slug})
        return path

