from dataclasses import dataclass


@dataclass(frozen=True)
class CreateSupplierDTO:
    business_id: int
    name: str

    phone: str = ""
    email: str = ""
    address: str = ""
    tax_number: str = ""
    notes: str = ""


@dataclass(frozen=True)
class UpdateSupplierDTO:
    business_id: int
    supplier_id: int
    name: str

    phone: str = ""
    email: str = ""
    address: str = ""
    tax_number: str = ""
    notes: str = ""
    is_active: bool = True


@dataclass(frozen=True)
class ListSuppliersQuery:
    business_id: int
    is_active: bool | None = None
    search: str | None = None
