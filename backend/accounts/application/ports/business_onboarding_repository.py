from typing import Protocol

from accounts.application.business_onboarding import CreatedBusiness


class BusinessOnboardingRepository(Protocol):
    def create_business_with_owner(
        self, *, user_id: int, name: str, number: str, address: str, logo: str | None
    ) -> CreatedBusiness: ...
