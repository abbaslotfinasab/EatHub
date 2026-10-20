from dataclasses import dataclass

from inventory.domain.exceptions import InvalidSourceIdentity


@dataclass(frozen=True, slots=True)
class SourceIdentity:
    business_id: int
    source_type: str
    source_document_id: int
    source_line_id: int
    operation_kind: str

    def __post_init__(self) -> None:
        for value, label in (
            (self.business_id, "Business ID"),
            (self.source_document_id, "Source document ID"),
            (self.source_line_id, "Source line ID"),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise InvalidSourceIdentity(f"{label} must be a positive integer.")
        if not isinstance(self.source_type, str) or not self.source_type.strip():
            raise InvalidSourceIdentity("Source type is required.")
        if not isinstance(self.operation_kind, str) or not self.operation_kind.strip():
            raise InvalidSourceIdentity("Operation kind is required.")
        object.__setattr__(self, "source_type", self.source_type.strip())
        object.__setattr__(self, "operation_kind", self.operation_kind.strip())
