from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CompoundMaterialComponentDTO:
    id: int
    ingredient_id: int
    ingredient_name: str
    quantity: Decimal
    unit: str
    material_type: str = "raw"


@dataclass(frozen=True, slots=True)
class CompoundMaterialDTO:
    id: int
    name: str
    sku: str | None
    unit: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    components: tuple[CompoundMaterialComponentDTO, ...]
    material_type: str = "compound"


@dataclass(frozen=True, slots=True)
class CompoundMaterialPageDTO:
    count: int
    page: int
    page_size: int
    results: list[CompoundMaterialDTO]
