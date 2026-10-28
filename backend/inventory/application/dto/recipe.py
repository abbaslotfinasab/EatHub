from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class RecipeLineDTO:
    id: int
    ingredient_id: int
    ingredient_name: str
    quantity: Decimal
    unit: str
    notes: str | None
    is_primary: bool = False
    material_type: str = "raw"


@dataclass(frozen=True, slots=True)
class RecipeDTO:
    id: int
    business_id: int
    name: str
    code: str | None
    type: str
    description: str | None
    is_active: bool
    inputs: tuple[RecipeLineDTO, ...]
    outputs: tuple[RecipeLineDTO, ...]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class RecipePageDTO:
    count: int
    page: int
    page_size: int
    results: tuple[RecipeDTO, ...]
