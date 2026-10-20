from dataclasses import dataclass

from inventory.domain.exceptions import InvalidMovement
from inventory.domain.value_objects.source_identity import SourceIdentity


@dataclass(frozen=True, slots=True)
class ReversalContext:
    """Application-provided facts needed to validate a reversal without a ledger."""

    latest_effective_source_identity: SourceIdentity | None
    already_reversed: bool

    def __post_init__(self) -> None:
        if self.latest_effective_source_identity is not None and not isinstance(
            self.latest_effective_source_identity, SourceIdentity
        ):
            raise InvalidMovement("Latest movement identity is invalid.")
        if not isinstance(self.already_reversed, bool):
            raise InvalidMovement("Already-reversed state must be boolean.")
