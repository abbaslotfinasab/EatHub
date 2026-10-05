from abc import ABC, abstractmethod
from decimal import Decimal


class PurchaseInvoiceQuantityReader(ABC):
    @abstractmethod
    def accepted_received_quantities(self, business_id: int, purchase_order_id: int) -> dict[int, Decimal]:
        raise NotImplementedError

    @abstractmethod
    def previously_invoiced_quantities(self, business_id: int, purchase_order_id: int, *, exclude_id: int | None = None) -> dict[int, Decimal]:
        raise NotImplementedError
