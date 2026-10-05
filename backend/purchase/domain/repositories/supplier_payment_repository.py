from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

from purchase.domain.entities.supplier_payment import SupplierPayment
from purchase.domain.enums.payment_method import PaymentMethod


class SupplierPaymentRepository(ABC):

    @abstractmethod
    def get_by_id_for_business(
        self,
        supplier_payment_id: int,
        business_id: int,
    ) -> SupplierPayment | None:
        """Return a supplier payment, including its allocations, within a business."""
        raise NotImplementedError

    @abstractmethod
    def list(
        self,
        business_id: int,
        *,
        supplier_id: int | None = None,
        invoice_id: int | None = None,
        method: PaymentMethod | None = None,
        payment_date_from: date | None = None,
        payment_date_to: date | None = None,
    ) -> list[SupplierPayment]:
        """Return supplier payments belonging to a business."""
        raise NotImplementedError

    @abstractmethod
    def total_allocated_to_invoice(
        self,
        business_id: int,
        invoice_id: int,
    ) -> Decimal:
        """Return the total payment amount allocated to an invoice in a business."""
        raise NotImplementedError

    @abstractmethod
    def save(
        self,
        supplier_payment: SupplierPayment,
    ) -> SupplierPayment:
        """Create or update a supplier payment together with its allocations."""
        raise NotImplementedError
