from dataclasses import dataclass


@dataclass(frozen=True)
class ListSupplierPaymentAllocationTotalsQuery:
    business_id: int
    supplier_payment_ids: list[int]
