from dataclasses import dataclass
from decimal import Decimal

from inventory.domain.value_objects.unit import Unit


@dataclass(frozen=True)
class StockBalanceDTO:
    id: int
    ingredient_id: int
    ingredient_name: str
    warehouse_id: int
    warehouse_name: str
    quantity: Decimal
    unit: Unit
    average_cost: Decimal


@dataclass(frozen=True)
class StockBalancePageDTO:
    count: int
    page: int
    page_size: int
    results: list[StockBalanceDTO]


@dataclass(frozen=True)
class ListStockBalancesQuery:
    business_id: int
    page: int = 1
    page_size: int = 20
    ingredient_id: int | None = None
    warehouse_id: int | None = None
