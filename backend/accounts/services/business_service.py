"""Deprecated compatibility facade for existing internal callers.

New presentation code must depend on the Accounts application use case.
"""

from accounts.composition import create_business
from accounts.models import Business


class BusinessService:
    @staticmethod
    def create_business(user, name, number="", address="", logo=None, request=None):
        result = create_business().execute(
            user_id=user.pk, name=name, number=number, address=address, logo=logo,
        )
        # Preserve the historical model return type for legacy test/support callers.
        return Business.objects.get(pk=result.business_id)
