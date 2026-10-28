from dataclasses import dataclass

from inventory.domain.exceptions import InactiveWarehouse, InvalidWarehouse


@dataclass(frozen=True, slots=True)
class Warehouse:
    id: int | None
    business_id: int
    name: str
    code: str | None = None
    is_active: bool = True
    is_default: bool = False

    def __post_init__(self) -> None:
        for value, label in (
            (self.id, "Warehouse ID"),
            (self.business_id, "Business ID"),
        ):
            if value is None and label == "Warehouse ID":
                continue
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise InvalidWarehouse(f"{label} must be a positive integer.")
        if not isinstance(self.name, str) or not self.name.strip():
            raise InvalidWarehouse("Warehouse name is required.")
        if (
            not isinstance(self.is_active, bool)
            or not isinstance(self.is_default, bool)
        ):
            raise InvalidWarehouse("Warehouse state flags must be boolean.")
        if self.code is not None and not isinstance(self.code, str):
            raise InvalidWarehouse("Warehouse code must be a string or None.")
        object.__setattr__(self, "name", self.name.strip())
        if self.code is not None:
            object.__setattr__(self, "code", self.code.strip() or None)

    def ensure_can_receive(self) -> None:
        if not self.is_active:
            raise InactiveWarehouse("Inactive warehouses cannot receive stock.")

    def ensure_active(self) -> None:
        if not self.is_active:
            raise InactiveWarehouse("Inactive warehouses cannot change stock.")
