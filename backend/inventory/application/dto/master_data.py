from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class InventoryItemDTO:
    id: int
    name: str
    sku: str | None
    unit: str
    preparation_level: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class WarehouseDTO:
    id: int
    name: str
    code: str | None
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime
