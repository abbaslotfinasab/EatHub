from dataclasses import dataclass

from inventory.application.exceptions import InvalidApplicationContext


@dataclass(frozen=True, slots=True)
class InventoryExecutionContext:
    """Trusted identity supplied by the outer authenticated application layer."""

    business_id: int
    actor_id: int | None = None

    def __post_init__(self) -> None:
        if (
            isinstance(self.business_id, bool)
            or not isinstance(self.business_id, int)
            or self.business_id <= 0
        ):
            raise InvalidApplicationContext("Business ID must be a positive integer.")
        if self.actor_id is not None and (
            isinstance(self.actor_id, bool)
            or not isinstance(self.actor_id, int)
            or self.actor_id <= 0
        ):
            raise InvalidApplicationContext("Actor ID must be a positive integer or None.")
