from dataclasses import dataclass
from decimal import Decimal

from purchase.domain.entities.purchase_invoice import PurchaseInvoice
from purchase.domain.enums.purchase_invoice_match_exception import (
    PurchaseInvoiceMatchException,
)
from purchase.domain.enums.purchase_invoice_matching_status import (
    PurchaseInvoiceMatchingStatus,
)

ZERO = Decimal("0")


@dataclass(frozen=True)
class PurchaseInvoiceMatchLineInput:
    invoice_item_id: int
    purchase_order_item_id: int
    ordered_quantity: Decimal
    accepted_received_quantity: Decimal
    previously_invoiced_quantity: Decimal
    current_invoice_quantity: Decimal
    purchase_order_unit_price: Decimal
    invoice_unit_price: Decimal


@dataclass(frozen=True)
class PurchaseInvoiceMatchLine:
    invoice_item_id: int
    purchase_order_item_id: int
    ordered_quantity: Decimal
    accepted_received_quantity: Decimal
    previously_invoiced_quantity: Decimal
    current_invoice_quantity: Decimal
    available_quantity: Decimal
    purchase_order_unit_price: Decimal
    invoice_unit_price: Decimal
    price_variance: Decimal
    exceptions: tuple[PurchaseInvoiceMatchException, ...]


@dataclass(frozen=True)
class PurchaseInvoiceMatchResult:
    invoice_id: int
    purchase_order_id: int
    status: PurchaseInvoiceMatchingStatus
    lines: tuple[PurchaseInvoiceMatchLine, ...]
    exceptions: tuple[PurchaseInvoiceMatchException, ...]


class PurchaseInvoiceMatcher:
    """Pure matching calculation over invoice and preloaded PO/receipt data."""

    def match(
        self,
        invoice: PurchaseInvoice,
        inputs: list[PurchaseInvoiceMatchLineInput],
    ) -> PurchaseInvoiceMatchResult:
        if invoice.id is None:
            raise ValueError("A persisted purchase invoice is required for matching.")
        if not inputs:
            raise ValueError("Purchase invoice must contain at least one item.")

        lines = []
        all_exceptions: list[PurchaseInvoiceMatchException] = []
        for data in inputs:
            available = data.accepted_received_quantity - data.previously_invoiced_quantity
            line_exceptions: list[PurchaseInvoiceMatchException] = []
            if data.accepted_received_quantity == ZERO:
                line_exceptions.append(PurchaseInvoiceMatchException.RECEIPT_PENDING)
            elif data.current_invoice_quantity > available:
                line_exceptions.append(PurchaseInvoiceMatchException.INVOICE_OVER_RECEIVED)

            variance = data.invoice_unit_price - data.purchase_order_unit_price
            if variance != ZERO:
                line_exceptions.append(PurchaseInvoiceMatchException.PRICE_VARIANCE)

            all_exceptions.extend(line_exceptions)
            lines.append(PurchaseInvoiceMatchLine(
                invoice_item_id=data.invoice_item_id,
                purchase_order_item_id=data.purchase_order_item_id,
                ordered_quantity=data.ordered_quantity,
                accepted_received_quantity=data.accepted_received_quantity,
                previously_invoiced_quantity=data.previously_invoiced_quantity,
                current_invoice_quantity=data.current_invoice_quantity,
                available_quantity=available,
                purchase_order_unit_price=data.purchase_order_unit_price,
                invoice_unit_price=data.invoice_unit_price,
                price_variance=variance,
                exceptions=tuple(line_exceptions),
            ))

        hard_exception = any(
            code in (
                PurchaseInvoiceMatchException.INVOICE_OVER_RECEIVED,
                PurchaseInvoiceMatchException.PRICE_VARIANCE,
            )
            for code in all_exceptions
        )
        if hard_exception:
            status = PurchaseInvoiceMatchingStatus.EXCEPTION
        elif PurchaseInvoiceMatchException.RECEIPT_PENDING in all_exceptions:
            status = PurchaseInvoiceMatchingStatus.PENDING_RECEIPT
        else:
            status = PurchaseInvoiceMatchingStatus.MATCHED

        return PurchaseInvoiceMatchResult(
            invoice_id=invoice.id,
            purchase_order_id=invoice.purchase_order_id,
            status=status,
            lines=tuple(lines),
            exceptions=tuple(dict.fromkeys(all_exceptions)),
        )
