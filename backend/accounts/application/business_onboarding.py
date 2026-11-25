"""Application use case for creating a business and its initial owner context."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CreatedBusiness:
    business_id: int
    business_name: str


class BusinessOnboardingRepository(Protocol):
    def create_business_with_owner(
        self, *, user_id: int, name: str, number: str, address: str, logo: str | None
    ) -> CreatedBusiness: ...


class CreateBusiness:
    def __init__(self, repository: BusinessOnboardingRepository) -> None:
        self._repository = repository

    def execute(
        self, *, user_id: int, name: str, number: str = "", address: str = "", logo: str | None = None
    ) -> CreatedBusiness:
        return self._repository.create_business_with_owner(
            user_id=user_id, name=name, number=number, address=address, logo=logo
        )
