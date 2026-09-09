# purchase/domain/entities/supplier.py

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Supplier:
    id: int | None
    business_id: int

    name: str

    phone: str = ""
    email: str = ""
    address: str = ""
    tax_number: str = ""

    is_active: bool = True

    notes: str = ""

    created_at: datetime | None = None
    updated_at: datetime | None = None