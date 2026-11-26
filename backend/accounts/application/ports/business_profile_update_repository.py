from typing import Protocol

from accounts.application.business_profile_update_result import (
    BusinessProfileUpdatePersistenceResult,
)


class BusinessProfileUpdateRepository(Protocol):
    def update_profile(
        self, *, business_id: int, changes: dict[str, object]
    ) -> BusinessProfileUpdatePersistenceResult | None:
        ...
