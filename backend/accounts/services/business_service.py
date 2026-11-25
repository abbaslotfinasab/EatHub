"""Deprecated compatibility facade for existing internal callers.

New presentation code must depend on the Accounts application use case.
"""

from accounts.infrastructure.django.business_onboarding_repository import DjangoBusinessOnboardingRepository


class BusinessService:
    @staticmethod
    def create_business(user, name, number="", address="", logo=None, request=None):
        return DjangoBusinessOnboardingRepository().create_business_with_owner_model(
            user_id=user.pk, name=name, number=number, address=address, logo=logo,
        )
