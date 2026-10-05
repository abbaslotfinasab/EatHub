from purchase.application.dto.purchase_invoice import CreatePurchaseInvoiceDTO
from purchase.domain.entities.purchase_invoice import PurchaseInvoice, PurchaseInvoiceItem
from purchase.domain.repositories.purchase_invoice_repository import PurchaseInvoiceRepository


class CreatePurchaseInvoiceUseCase:
    def __init__(self, repository: PurchaseInvoiceRepository) -> None:
        self._repository = repository

    def execute(self, command: CreatePurchaseInvoiceDTO) -> PurchaseInvoice:
        items = [PurchaseInvoiceItem(
            ingredient_id=item.ingredient_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            description=item.description,
            discount_percent=item.discount_percent,
            tax_percent=item.tax_percent,
        ) for item in command.items]
        invoice = PurchaseInvoice(
            id=None,
            business_id=command.business_id,
            supplier_id=command.supplier_id,
            invoice_number=command.invoice_number,
            invoice_date=command.invoice_date,
            purchase_order_id=command.purchase_order_id,
            discount_percent=command.discount_percent,
            tax_percent=command.tax_percent,
            items=items,
        )
        return self._repository.save(invoice)
