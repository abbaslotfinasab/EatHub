from dataclasses import dataclass

from inventory.domain.exceptions import InvalidStockKey


def _positive_id(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise InvalidStockKey(f"{field_name} must be a positive integer.")


@dataclass(frozen=True, slots=True)
class StockKey:
    business_id: int
    warehouse_id: int
    ingredient_id: int

    def __post_init__(self) -> None:
        _positive_id(self.business_id, "Business ID")
        _positive_id(self.warehouse_id, "Warehouse ID")
        _positive_id(self.ingredient_id, "Ingredient ID")
