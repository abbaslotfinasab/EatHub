from dataclasses import dataclass


@dataclass(frozen=True)
class BusinessProfileUpdatePersistenceResult:
    previous_logo_path: str | None
