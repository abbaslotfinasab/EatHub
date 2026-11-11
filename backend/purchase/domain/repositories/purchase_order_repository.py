from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

from purchase.domain.entities.purchase_order import PurchaseOrder
from purchase.domain.enums.purchase_order_status import (
    PurchaseOrderStatus,
)


class PurchaseOrderRepository(ABC):

    @abstractmethod
    def get_by_id_for_business(
        self,
        purchase_order_id: int,
        business_id: int,
    ) -> PurchaseOrder | None:
        """
        Return a purchase order belonging to
        a specific business.

        The returned aggregate must include
        its purchase order items.
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_id_for_business_for_update(
        self,
        purchase_order_id: int,
        business_id: int,
    ) -> PurchaseOrder | None:
        """Load and lock the tenant-scoped PO root for a transactional workflow."""
        raise NotImplementedError

    @abstractmethod
    def list(
        self,
        business_id: int,
        *,
        status: PurchaseOrderStatus | None = None,
        supplier_id: int | None = None,
        requisition_id: int | None = None,
        order_date_from: date | None = None,
        order_date_to: date | None = None,
    ) -> list[PurchaseOrder]:
        """
        Return purchase orders for a business.
        """
        raise NotImplementedError

    @abstractmethod
    def get_ordered_quantities_by_requisition(
        self,
        business_id: int,
        requisition_id: int,
    ) -> dict[int, Decimal]:
        """Return non-cancelled ordered quantities grouped by ingredient."""
        raise NotImplementedError

    @abstractmethod
    def save(
        self,
        purchase_order: PurchaseOrder,
    ) -> PurchaseOrder:
        """
        Create or update a purchase order
        together with its items.
        """
        raise NotImplementedError

    @abstractmethod
    def save_for_requisition(
        self,
        purchase_order: PurchaseOrder,
    ) -> PurchaseOrder:
        """Atomically validate remaining quantities and persist a requisition PO."""
        raise NotImplementedError
