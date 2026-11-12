import type {
    PurchaseInvoice,
    PurchaseInvoiceInput,
    PurchaseInvoiceMatchResponse,
} from '../../domain/entities/inventory/PurchaseInvoice.ts';
import type {
    PurchaseInvoiceRepository,
    PurchaseInvoiceFilters,
} from '../../domain/repositories/inventory/PurchaseInvoiceRepository.ts';
import type {
    PostPurchaseInvoiceResponseDTO,
    PurchaseInvoiceDTO,
    PurchaseInvoiceMatchResponseDTO,
    PurchaseInvoiceWriteDTO,
} from '../dtos/purchase/PurchaseInvoiceDTO.ts';
import { PurchaseInvoiceRemoteDataSource } from '../datasources/PurchaseInvoiceRemoteDataSource.ts';

const mapInvoice = (dto: PurchaseInvoiceDTO): PurchaseInvoice => ({
    id: String(dto.id),
    businessId: String(dto.business_id),
    supplierId: String(dto.supplier_id),
    purchaseOrderId: String(dto.purchase_order_id),
    invoiceNumber: dto.invoice_number,
    invoiceDate: dto.invoice_date,
    status: dto.status,
    approvedAt: dto.approved_at,
    approvedById: dto.approved_by_id === null ? null : String(dto.approved_by_id),
    postedAt: dto.posted_at,
    postedById: dto.posted_by_id === null ? null : String(dto.posted_by_id),
    cancelledAt: dto.cancelled_at,
    cancelledById: dto.cancelled_by_id === null ? null : String(dto.cancelled_by_id),
    cancellationReason: dto.cancellation_reason,
    matchingStatus: dto.matching_status,
    matchedAt: dto.matched_at,
    subtotal: dto.subtotal,
    discountPercent: dto.discount_percent,
    discountAmount: dto.discount_amount,
    taxPercent: dto.tax_percent,
    taxAmount: dto.tax_amount,
    totalPrice: dto.total_price,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
    items: dto.items.map((item) => ({
        id: String(item.id),
        ingredientId: String(item.ingredient_id),
        purchaseOrderItemId: String(item.purchase_order_item_id),
        description: item.description,
        quantity: item.quantity,
        unitPrice: item.unit_price,
        discountPercent: item.discount_percent,
        discountAmount: item.discount_amount,
        taxPercent: item.tax_percent,
        taxAmount: item.tax_amount,
        subtotal: item.subtotal,
        totalPrice: item.total_price,
    })),
});

const toWriteDTO = (input: PurchaseInvoiceInput): PurchaseInvoiceWriteDTO => ({
    supplier_id: Number(input.supplierId),
    purchase_order_id: Number(input.purchaseOrderId),
    invoice_number: input.invoiceNumber.trim(),
    invoice_date: input.invoiceDate,
    discount_percent: input.discountPercent || '0',
    tax_percent: input.taxPercent || '0',
    items: input.items.map((item) => ({
        ingredient_id: Number(item.ingredientId),
        purchase_order_item_id: Number(item.purchaseOrderItemId),
        quantity: item.quantity,
        unit_price: item.unitPrice,
        description: item.description.trim(),
        discount_percent: item.discountPercent || '0',
        tax_percent: item.taxPercent || '0',
    })),
});

const mapMatch = (dto: PurchaseInvoiceMatchResponseDTO): PurchaseInvoiceMatchResponse => ({
    current: {
        invoiceId: String(dto.current.invoice_id),
        purchaseOrderId: String(dto.current.purchase_order_id),
        status: dto.current.status,
        exceptions: dto.current.exceptions,
        lines: dto.current.lines.map((line) => ({
            invoiceItemId: String(line.invoice_item_id),
            purchaseOrderItemId: String(line.purchase_order_item_id),
            orderedQuantity: line.ordered_quantity,
            acceptedReceivedQuantity: line.accepted_received_quantity,
            previouslyInvoicedQuantity: line.previously_invoiced_quantity,
            currentInvoiceQuantity: line.current_invoice_quantity,
            availableQuantity: line.available_quantity,
            purchaseOrderUnitPrice: line.purchase_order_unit_price,
            invoiceUnitPrice: line.invoice_unit_price,
            priceVariance: line.price_variance,
            exceptions: line.exceptions,
        })),
    },
    lastPersisted: {
        status: dto.last_persisted.status,
        matchedAt: dto.last_persisted.matched_at,
    },
});

export class PurchaseInvoiceRepositoryImpl implements PurchaseInvoiceRepository {
    constructor(private readonly remote = new PurchaseInvoiceRemoteDataSource()) {}

    async list(filters?: PurchaseInvoiceFilters): Promise<PurchaseInvoice[]> {
        return (await this.remote.list(filters)).map(mapInvoice);
    }

    async get(id: string): Promise<PurchaseInvoice> {
        return mapInvoice(await this.remote.get(id));
    }

    async create(input: PurchaseInvoiceInput): Promise<PurchaseInvoice> {
        return mapInvoice(await this.remote.create(toWriteDTO(input)));
    }

    async update(id: string, input: PurchaseInvoiceInput): Promise<PurchaseInvoice> {
        return mapInvoice(await this.remote.update(id, toWriteDTO(input)));
    }

    async approve(id: string): Promise<PurchaseInvoice> {
        return mapInvoice(await this.remote.approve(id));
    }

    async match(id: string, persist: boolean): Promise<PurchaseInvoiceMatchResponse> {
        return mapMatch(await this.remote.match(id, persist));
    }

    async post(id: string, dueDate?: string): Promise<PurchaseInvoice> {
        const result: PostPurchaseInvoiceResponseDTO = await this.remote.post(id, dueDate);
        return mapInvoice(result.invoice);
    }

    async cancel(id: string, reason: string): Promise<PurchaseInvoice> {
        return mapInvoice(await this.remote.cancel(id, reason));
    }
}
