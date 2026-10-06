from purchase.application.dto.purchase_invoice import UpdatePurchaseInvoiceDTO
from purchase.domain.entities.purchase_invoice import (
    PurchaseInvoiceItem,
)
from purchase.domain.repositories.purchase_invoice_repository import (
    PurchaseInvoiceRepository,
)


class UpdatePurchaseInvoiceUseCase:
    def __init__(self, repository: PurchaseInvoiceRepository) -> None:
        self._repository = repository

    def execute(self, command: UpdatePurchaseInvoiceDTO):
        self._validate_positive_id(command.business_id, "Business ID")
        self._validate_positive_id(
            command.purchase_invoice_id,
            "Purchase invoice ID",
        )
        invoice = self._repository.get_by_id_for_business(
            command.purchase_invoice_id,
            command.business_id,
        )
        if invoice is None:
            raise ValueError("Purchase invoice does not exist in this business.")

        items = [
            PurchaseInvoiceItem(
                ingredient_id=item.ingredient_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                purchase_order_item_id=item.purchase_order_item_id,
                description=item.description,
                discount_percent=item.discount_percent,
                tax_percent=item.tax_percent,
            )
            for item in command.items
        ]
        invoice.update_details(
            supplier_id=command.supplier_id,
            invoice_number=command.invoice_number,
            invoice_date=command.invoice_date,
            purchase_order_id=command.purchase_order_id,
            discount_percent=command.discount_percent,
            tax_percent=command.tax_percent,
            items=items,
        )
        return self._repository.save(invoice)

    @staticmethod
    def _validate_positive_id(value: int, field_name: str) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")
